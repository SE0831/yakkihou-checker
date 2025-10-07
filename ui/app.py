# ui/app.py
import requests
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import io

st.set_page_config(page_title="薬機・景表チェッカー", layout="wide")

# ===== ユーティリティ =====
SEVERITY_ORDER = {"high": 2, "mid": 1, "low": 0}
SEVERITY_JP = {"high": "高", "mid": "中", "low": "低"}
LAW_JP = {"yakki": "薬機", "keihyo": "景表"}
SEV_COLOR = {"high": "#ffccd5", "mid": "#ffe5b4", "low": "#fff3b0"}  # 高リスクほど濃い

def to_df(spans: List[Dict[str, Any]]) -> pd.DataFrame:
    if not spans:
        return pd.DataFrame(columns=[
            "一致文字列","ラベル","重要度","法令","ルールID","提案","注記","start","end","_sev","_law","_sev_rank","_badge"
        ])
    rows = []
    for s in spans:
        sev = s.get("severity","low")
        rows.append({
            "一致文字列": s.get("matched",""),
            "ラベル": s.get("label",""),
            "重要度": SEVERITY_JP.get(sev, sev),
            "法令": LAW_JP.get(s.get("law",""), s.get("law","")),
            "ルールID": s.get("rule_id",""),
            "提案": s.get("suggest",""),
            "注記": s.get("note",""),
            "start": s.get("start",0),
            "end": s.get("end",0),
            "_sev": sev,
            "_law": s.get("law",""),
            "_sev_rank": SEVERITY_ORDER.get(sev, 0),
            "_badge": {"high":"🟥 高","mid":"🟧 中","low":"🟨 低"}.get(sev,"🟨 低"),
        })
    df = pd.DataFrame(rows).sort_values(by=["_sev_rank","start"], ascending=[False, True]).reset_index(drop=True)
    return df

def paint_text(text: str, df_view: pd.DataFrame) -> str:
    """本文をハイライト（重要度ごとに色分け）"""
    if df_view.empty:
        return text
    marks = []
    for _, r in df_view.iterrows():
        marks.append((int(r["start"]), int(r["end"]), r.get("_sev","low")))
    marks.sort(key=lambda x: x[0])
    out, cur = [], 0
    for s, e, sev in marks:
        s = max(0, min(s, len(text)))
        e = max(0, min(e, len(text)))
        if cur < s:
            out.append(text[cur:s])
        color = SEV_COLOR.get(sev, "#fff3b0")
        out.append(f'<mark style="background:{color}; padding:0 2px; border-radius:3px;">{text[s:e]}</mark>')
        cur = e
    out.append(text[cur:])
    return "".join(out)

def build_clipboard_summary(df: pd.DataFrame) -> str:
    if df.empty:
        return "NG表現は検出されませんでした。"
    lines = ["【検出サマリー】"]
    for _, r in df.iterrows():
        lines.append(f"- [{r['_badge']}/{r['法令']}] {r['一致文字列']}｜{r['ラベル']}（{r['ルールID']}）\n  提案: {r['提案']}")
    return "\n".join(lines)

def csv_bytes_for_excel(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    cols = ["一致文字列","ラベル","重要度","法令","ルールID","提案","注記","start","end"]
    (df[cols] if set(cols).issubset(df.columns) else df).to_csv(buf, index=False, encoding="utf-8-sig")
    return buf.getvalue().encode("utf-8-sig")

# ===== ヘッダー =====
st.title("🛡️ 薬機・景表チェッカー")
st.caption("広告文を入力すると、要注意表現を自動で検出します。")

# ===== サイドバー（設定） =====
with st.sidebar:
    st.header("設定")
    api_base = st.text_input("APIのURL", "http://127.0.0.1:8000/api", help="通常はこのままでOK")

    # フィルタ（変更すると即リレンダリング）—— 解析結果はセッションに保持されるのでAPI再呼び出し不要
    st.markdown("### 表示フィルタ")
    sev_selected = st.multiselect("重要度で絞り込み", options=["高","中","低"], default=["高","中","低"])
    law_selected = st.multiselect("法令で絞り込み", options=["薬機","景表"], default=["薬機","景表"])

    st.markdown("---")
    st.subheader("サンプル文を挿入")
    if st.button("例1：痩身広告"):
        st.session_state["text"] = "必ず痩せます。医師推薦。たった1週間で10kg減。"
    if st.button("例2：美容系"):
        st.session_state["text"] = "このクリームでシミが消えます。完全に治ります。"

# ===== 入力 =====
text = st.text_area(
    "① 解析する広告文を貼り付けてください",
    value=st.session_state.get("text", ""),
    height=180,
    placeholder="例）必ず痩せます。医師推薦。たった1週間で10kg減。",
)

col_run, col_clear = st.columns([1, 1])
run = col_run.button("② 解析する", type="primary")
if col_clear.button("クリア"):
    st.session_state["text"] = ""
    # 結果も消す
    st.session_state.pop("result", None)
    st.rerun()

# ===== API呼び出し関数 =====
def call_api(api_base_url: str, text_in: str):
    url = f"{api_base_url}/analyze"
    return requests.post(url, json={"text": text_in}, timeout=30)

# ===== 解析の実行（押したときだけ呼ぶ → 結果はセッションに保存） =====
if run:
    if not text.strip():
        st.warning("テキストを入力してください。")
    else:
        with st.spinner("解析中…"):
            try:
                r = call_api(api_base, text)
            except Exception as e:
                st.error(f"APIへの接続に失敗しました：{e}")
                st.stop()

        if r.status_code != 200:
            st.error(f"APIエラー：{r.status_code} / {r.text}")
            st.stop()

        st.session_state["result"] = r.json()
        st.session_state["text_saved"] = text  # 解析時点の本文も保存
        st.success("解析が完了しました。サイドバーのフィルタを切り替えると即時反映されます。")

# ===== 以降は「セッションに結果があれば描画」→ フィルタ変更で即時反映 =====
result = st.session_state.get("result")
base_text = st.session_state.get("text_saved", text)

if result is None:
    st.info("まだ解析結果がありません。テキストを入力して「② 解析する」を押してください。")
else:
    # ===== 概要（左）＋ ダウンロード（右） =====
    left, right = st.columns([2, 1])
    with left:
        st.subheader("③ 解析結果のサマリー")
        score = int(result.get("score", 0))
        st.metric("リスクスコア（0-100）", score)
        # ★ ② 視覚化：進捗ゲージ（色はデフォルトでも直感的）
        st.progress(min(max(score, 0), 100) / 100)
        hit_count = len(result.get("spans", []))
        st.write(f"検出件数：**{hit_count} 件**")

    with right:
        if hit_count:
            df_all = to_df(result.get("spans", []))
            st.download_button(
                "結果をCSVでダウンロード",
                csv_bytes_for_excel(df_all),
                file_name="yakkihou_result.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.markdown("---")

    # ===== 検出一覧（表＋カード） =====
    st.subheader("④ 検出された表現（一覧）")
    df_all = to_df(result.get("spans", []))

    # ★ ① フィルタ：サイドバーの選択だけで即座に反映（API再呼出しなし）
    mask = df_all["重要度"].isin(sev_selected) & df_all["法令"].isin(law_selected)
    df_view = df_all[mask].copy().reset_index(drop=True)

    if df_view.empty:
        st.success("問題のある表現は検出されませんでした ✅")
    else:
        # 表に色付きバッジ列を追加（DataFrameは絵文字ならOK）
        show_df = df_view.drop(columns=["_sev","_law","_sev_rank"], errors="ignore").copy()
        show_df.insert(2, "重要度バッジ", df_view["_badge"])
        st.dataframe(show_df, use_container_width=True, hide_index=True)

        # カード風
        st.markdown("###### カード表示（詳細）")
        for _, s in df_view.iterrows():
            badge = s["_badge"]
            with st.container(border=True):
                st.markdown(
                    f"**{badge} {s['ラベル']}** — `{s['一致文字列']}` "
                    f"(法令: {s['法令']} / ルール: {s['ルールID']})"
                )
                if s["提案"]:
                    st.caption(f"💡 提案: {s['提案']}")
                if s["注記"]:
                    st.caption(f"📝 注記: {s['注記']}")

        # コピー用
        with st.expander("結果をコピー（共有用）"):
            st.text_area(
                "以下をコピーしてチャット・メールに貼り付けできます。",
                build_clipboard_summary(df_view),
                height=200,
            )

    st.markdown("---")

    # ===== ハイライト表示 =====
    st.subheader("⑤ 入力文のハイライト")
    colored_html = paint_text(base_text, df_view)
    st.markdown(f"<div style='line-height:1.9'>{colored_html}</div>", unsafe_allow_html=True)
    st.info("※ 色の濃い順に重要度が高い表現です。")
