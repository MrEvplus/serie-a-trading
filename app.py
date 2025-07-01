import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Serie A Trading Dashboard", layout="wide")

# -------------------------------
# CARICAMENTO FILE EXCEL DAL REPO
# -------------------------------
# Carico SEMPRE il file Excel dal repository
df_all = pd.read_excel("serie a 20-25.xlsx", sheet_name=None)
df = list(df_all.values())[0]

st.success("✅ File Excel caricato dal repository!")

# Trasformazioni iniziali
df["datameci"] = pd.to_datetime(df["datameci"], errors="coerce")
df["goals_ft"] = df["scor1"] + df["scor2"]
df["goals_1t"] = df["scorp1"] + df["scorp2"]
df["goals_2t"] = df["goals_ft"] - df["goals_1t"]

df["esito"] = np.where(
    df["scor1"] > df["scor2"], "Win",
    np.where(df["scor1"] == df["scor2"], "Draw", "Lose")
)

df["btts"] = np.where(
    (df["scor1"] > 0) & (df["scor2"] > 0), "Yes", "No"
)

squadre = sorted(set(df["txtechipa1"]).union(df["txtechipa2"]))

st.sidebar.title("🔍 Navigazione")
page = st.sidebar.radio("Vai a:", ["Macro ROI Analysis", "Dashboard CornerProBet"])

# --------------------------
# PAGE 1 - ROI MACRO ANALYSIS
# --------------------------
if page == "Macro ROI Analysis":
    st.header("📊 Macro ROI Analysis")

    squadra_sel = st.selectbox("Seleziona squadra (Home o Away):", squadre)
    side = st.radio("Partite in casa o trasferta?", ["Home", "Away"])

    quota_ranges = {
        "1.01-1.49": (1.01, 1.49),
        "1.50-1.99": (1.50, 1.99),
        "2.00-3.00": (2.00, 3.00),
        "3.01-5.00": (3.01, 5.00),
        "5.01-10.00": (5.01, 10.00),
        ">10.00": (10.01, 100.00)
    }

    quota_sel = st.multiselect(
        "Seleziona range quote:",
        list(quota_ranges.keys()),
        default=list(quota_ranges.keys())
    )

    quota_tipo = st.selectbox(
        "Quota su cui calcolare ROI:",
        ["cotaa (Home)", "cotae (Draw)", "cotad (Away)"]
    )

    if side == "Home":
        df_team = df[df["txtechipa1"] == squadra_sel].copy()
    else:
        df_team = df[df["txtechipa2"] == squadra_sel].copy()

    if quota_tipo.startswith("cotaa"):
        df_team["quota"] = df_team["cotaa"]
        esito_match = "Win"
    elif quota_tipo.startswith("cotae"):
        df_team["quota"] = df_team["cotae"]
        esito_match = "Draw"
    else:
        df_team["quota"] = df_team["cotad"]
        esito_match = "Lose" if side == "Home" else "Win"

    mask = pd.Series(False, index=df_team.index)
    for r in quota_sel:
        min_q, max_q = quota_ranges[r]
        mask |= (df_team["quota"] >= min_q) & (df_team["quota"] <= max_q)

    df_team = df_team[mask]

    st.write(f"Partite trovate: {len(df_team)}")

    if len(df_team) > 0:
        df_team["back_profit"] = np.where(
            df_team["esito"] == esito_match,
            (df_team["quota"] - 1) * 10,
            -10
        )
        roi_back = df_team["back_profit"].sum() / (10 * len(df_team)) * 100

        df_team["lay_profit"] = np.where(
            df_team["esito"] != esito_match,
            10,
            - (df_team["quota"] - 1) * 10
        )
        roi_lay = df_team["lay_profit"].sum() / (10 * len(df_team)) * 100

        st.metric("ROI Back", f"{roi_back:.2f}%")
        st.metric("ROI Lay", f"{roi_lay:.2f}%")

        st.dataframe(
            df_team[[
                "datameci", "txtechipa1", "txtechipa2",
                "quota", "scor1", "scor2", "esito"
            ]].sort_values("datameci", ascending=False)
        )
    else:
        st.info("Nessuna partita trovata per questi filtri.")

# --------------------------
# PAGE 2 - CORNERPROBET STYLE
# --------------------------
elif page == "Dashboard CornerProBet":
    st.header("📊 Dashboard Stile CornerProBet")

    squadra_home = st.selectbox("Seleziona squadra HOME:", squadre)
    squadra_away = st.selectbox("Seleziona squadra AWAY:", squadre)

    mask = (
        (df["txtechipa1"] == squadra_home) &
        (df["txtechipa2"] == squadra_away)
    )
    df_match = df[mask]

    st.write(f"Partite trovate: {len(df_match)}")

    if len(df_match) > 0:

        # Correct Score Distribution
        st.subheader("Correct Score Distribution")
        df_match["correct_score"] = df_match["scor1"].astype(str) + "-" + df_match["scor2"].astype(str)
        score_counts = df_match["correct_score"].value_counts().reset_index()
        score_counts.columns = ["Score", "Count"]
        score_counts["%"] = (score_counts["Count"] / score_counts["Count"].sum()) * 100
        st.dataframe(score_counts)

        fig_score = px.pie(
            score_counts.head(10),
            names="Score",
            values="Count",
            title="Top 10 Most Frequent Correct Scores"
        )
        st.plotly_chart(fig_score, use_container_width=True)

        # Over/Under
        st.subheader("Over/Under Stats")
        over_soglie = [0.5, 1.5, 2.5, 3.5, 4.5]
        over_data = []
        for soglia in over_soglie:
            perc = (df_match["goals_ft"] > soglia).mean() * 100
            over_data.append({"Over": f"Over {soglia}", "Percentage": perc})
        df_over = pd.DataFrame(over_data)
        fig_over = px.bar(df_over, x="Over", y="Percentage", title="Over/Under FT %")
        st.plotly_chart(fig_over, use_container_width=True)

        # Over split 1T e 2T
        st.subheader("Over per tempo")
        over_data_1t = []
        over_data_2t = []
        for soglia in over_soglie:
            perc_1t = (df_match["goals_1t"] > soglia).mean() * 100
            perc_2t = (df_match["goals_2t"] > soglia).mean() * 100
            over_data_1t.append({"Over": f"Over {soglia}", "Percentage": perc_1t})
            over_data_2t.append({"Over": f"Over {soglia}", "Percentage": perc_2t})
        fig_1t = px.bar(pd.DataFrame(over_data_1t), x="Over", y="Percentage", title="Over 1° Tempo %")
        fig_2t = px.bar(pd.DataFrame(over_data_2t), x="Over", y="Percentage", title="Over 2° Tempo %")
        st.plotly_chart(fig_1t, use_container_width=True)
        st.plotly_chart(fig_2t, use_container_width=True)

        # BTTS
        st.subheader("BTTS")
        btts_pct = (df_match["btts"] == "Yes").mean() * 100
        st.metric("BTTS %", f"{btts_pct:.2f}%")

        # Time Frame Goals
        st.subheader("First Goal Time Frame")
        gh1 = df_match["gh1"].dropna()
        ga1 = df_match["ga1"].dropna()
        first_goals = pd.concat([gh1, ga1], ignore_index=True)
        time_bins = [0,15,30,45,60,75,90,120]
        bin_labels = ["0-15","16-30","31-45","46-60","61-75","76-90","91+"]
        bins = pd.cut(first_goals, bins=time_bins, labels=bin_labels, include_lowest=True)
        first_goal_counts = bins.value_counts(normalize=True).sort_index()*100
        st.bar_chart(first_goal_counts)

        # Goal Conversion Rate
        st.subheader("Goal Conversion Rate")
        total_shots = df_match["suth"].sum() + df_match["suta"].sum()
        total_goals = df_match["scor1"].sum() + df_match["scor2"].sum()
        conversion_rate = (total_goals / total_shots * 100) if total_shots > 0 else 0
        st.metric("Goal Conversion %", f"{conversion_rate:.2f}%")

        # Corners
        st.subheader("Corners Analysis")
        corner_mean_home = df_match["corh"].mean()
        corner_mean_away = df_match["cora"].mean()
        st.write(f"Corner medi HOME: {corner_mean_home:.2f}")
        st.write(f"Corner medi AWAY: {corner_mean_away:.2f}")

        # Yellow Cards
        st.subheader("Yellow Cards")
        yellow_home = df_match["yellowh"].mean()
        yellow_away = df_match["yellowa"].mean()
        st.write(f"Cartellini HOME: {yellow_home:.2f}")
        st.write(f"Cartellini AWAY: {yellow_away:.2f}")

        # Possession
        if "ballph" in df_match.columns and "ballpa" in df_match.columns:
            st.subheader("Possession %")
            poss_home = df_match["ballph"].mean()
            poss_away = df_match["ballpa"].mean()
            st.write(f"Possesso palla HOME: {poss_home:.2f}%")
            st.write(f"Possesso palla AWAY: {poss_away:.2f}%")

        # Head-to-Head Aggregato
        st.subheader("Head-to-Head Aggregato")
        esiti_counts = df_match["esito"].value_counts(normalize=True) * 100
        fig_esiti = px.pie(
            names=esiti_counts.index,
            values=esiti_counts.values,
            title="Distribuzione risultati storici (Head-to-Head)"
        )
        st.plotly_chart(fig_esiti, use_container_width=True)

        # Gol tardivi
        st.subheader("Gol Tardivi (dopo 76')")
        late_goals = pd.concat([
            df_match.loc[:, ["gh1","gh2","gh3","gh4","gh5","gh6","gh7","gh8","gh9"]],
            df_match.loc[:, ["ga1","ga2","ga3","ga4","ga5","ga6","ga7","ga8","ga9"]]
        ], axis=1).stack().dropna()
        late_goals_pct = (late_goals > 75).mean() * 100
        st.metric("Gol dopo 76° minuto", f"{late_goals_pct:.2f}%")

        # Head-to-Head dettaglio
        st.subheader("Head-to-Head Dettaglio")
        st.dataframe(
            df_match[[
                "datameci", "txtechipa1", "txtechipa2",
                "scor1", "scor2"
            ]].sort_values("datameci", ascending=False)
        )
    else:
        st.info("Nessuna partita trovata fra queste squadre.")
else:
    st.info("Caricamento file Excel non riuscito.")
