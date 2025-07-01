import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Serie A Trading Dashboard", layout="wide")

# -------------------------------
# CARICAMENTO FILE EXCEL DAL REPO
# -------------------------------
df_all = pd.read_excel("serie a 20-25.xlsx", sheet_name=None)
df = list(df_all.values())[0]

st.success("✅ File Excel caricato dal repository!")

# Visualizza intestazioni per debug
# st.write("Colonne trovate nel file:", df.columns.tolist())

# Conversione Data
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

# Calcoli base
df["Goals FT"] = df["Home Goal FT"] + df["Away Goal FT"]
df["Goals 1T"] = df["Home Goal 1T"] + df["Away Goal 1T"]
df["Goals 2T"] = df["Goals FT"] - df["Goals 1T"]

# Esito finale
df["Esito"] = np.where(
    df["Home Goal FT"] > df["Away Goal FT"], "Win",
    np.where(df["Home Goal FT"] == df["Away Goal FT"], "Draw", "Lose")
)

# BTTS
df["BTTS"] = np.where(
    (df["Home Goal FT"] > 0) & (df["Away Goal FT"] > 0),
    "Yes", "No"
)

# Squadre uniche
squadre = sorted(set(df["Home"]).union(df["Away"]))

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
        ["Odd home", "Odd Draw", "Odd Away"]
    )

    if side == "Home":
        df_team = df[df["Home"] == squadra_sel].copy()
    else:
        df_team = df[df["Away"] == squadra_sel].copy()

    df_team["Quota"] = df_team[quota_tipo]

    mask = pd.Series(False, index=df_team.index)
    for r in quota_sel:
        min_q, max_q = quota_ranges[r]
        mask |= (df_team["Quota"] >= min_q) & (df_team["Quota"] <= max_q)

    df_team = df_team[mask]

    st.write(f"Partite trovate: {len(df_team)}")

    if len(df_team) > 0:
        if quota_tipo == "Odd home":
            esito_match = "Win"
        elif quota_tipo == "Odd Draw":
            esito_match = "Draw"
        else:
            esito_match = "Lose" if side == "Home" else "Win"

        df_team["Back Profit"] = np.where(
            df_team["Esito"] == esito_match,
            (df_team["Quota"] - 1) * 10,
            -10
        )
        roi_back = df_team["Back Profit"].sum() / (10 * len(df_team)) * 100

        df_team["Lay Profit"] = np.where(
            df_team["Esito"] != esito_match,
            10,
            - (df_team["Quota"] - 1) * 10
        )
        roi_lay = df_team["Lay Profit"].sum() / (10 * len(df_team)) * 100

        st.metric("ROI Back", f"{roi_back:.2f}%")
        st.metric("ROI Lay", f"{roi_lay:.2f}%")

        st.dataframe(
            df_team[[
                "Data", "Home", "Away", "Quota",
                "Home Goal FT", "Away Goal FT", "Esito"
            ]].sort_values("Data", ascending=False)
        )

        # ------------------------------
        # TIME FRAME ANALYSIS su df_team
        # ------------------------------

        st.subheader("⚽ Distribuzione Time Frame Goals (Squadra Selezionata)")

        if side == "Home":
            # Goals fatti = home goals
            goal_cols_fatti = [
                "home 1 goal segnato (min)",
                "home 2 goal segnato(min)",
                "home 3 goal segnato(min)",
                "home 4 goal segnato(min)",
                "home 5 goal segnato(min)",
                "home 6 goal segnato(min)",
                "home 7 goal segnato(min)",
                "home 8 goal segnato(min)",
                "home 9 goal segnato(min)"
            ]
            # Goals subiti = away goals
            goal_cols_subiti = [
                "1  goal away (min)",
                "2  goal away (min)",
                "3 goal away (min)",
                "4  goal away (min)",
                "5  goal away (min)",
                "6  goal away (min)",
                "7  goal away (min)",
                "8  goal away (min)",
                "9  goal away (min)"
            ]
        else:
            # Goals fatti = away goals
            goal_cols_fatti = [
                "1  goal away (min)",
                "2  goal away (min)",
                "3 goal away (min)",
                "4  goal away (min)",
                "5  goal away (min)",
                "6  goal away (min)",
                "7  goal away (min)",
                "8  goal away (min)",
                "9  goal away (min)"
            ]
            # Goals subiti = home goals
            goal_cols_subiti = [
                "home 1 goal segnato (min)",
                "home 2 goal segnato(min)",
                "home 3 goal segnato(min)",
                "home 4 goal segnato(min)",
                "home 5 goal segnato(min)",
                "home 6 goal segnato(min)",
                "home 7 goal segnato(min)",
                "home 8 goal segnato(min)",
                "home 9 goal segnato(min)"
            ]

        # Stack goals fatti e subiti
        goals_fatti = df_team[goal_cols_fatti].stack().dropna()
        goals_subiti = df_team[goal_cols_subiti].stack().dropna()

        bins = [0,15,30,45,60,75,90,120]
        labels = ["0-15","16-30","31-45","46-60","61-75","76-90","91+"]

        fatti_bins = pd.cut(goals_fatti, bins=bins, labels=labels, right=True)
        fatti_counts = fatti_bins.value_counts(normalize=True).sort_index() * 100

        subiti_bins = pd.cut(goals_subiti, bins=bins, labels=labels, right=True)
        subiti_counts = subiti_bins.value_counts(normalize=True).sort_index() * 100

        df_timeframe_db = pd.DataFrame({
            "Time Frame": labels,
            "Goals FATTI (%)": fatti_counts.reindex(labels).fillna(0).values,
            "Goals SUBITI (%)": subiti_counts.reindex(labels).fillna(0).values
        })

        st.dataframe(df_timeframe_db)

        fig_time_db = px.bar(
            df_timeframe_db,
            x="Time Frame",
            y=["Goals FATTI (%)", "Goals SUBITI (%)"],
            barmode="group",
            title=f"Distribuzione Time Frame - {squadra_sel} ({side})"
        )
        st.plotly_chart(fig_time_db, use_container_width=True)

    else:
        st.info("Nessuna partita trovata per questi filtri.")

# --------------------------
# PAGE 2 - DASHBOARD CORNERPROBET
# --------------------------
elif page == "Dashboard CornerProBet":
    st.header("📊 Dashboard stile CornerProBet")

    squadra_home = st.selectbox("Seleziona squadra HOME:", squadre)
    squadra_away = st.selectbox("Seleziona squadra AWAY:", squadre)

    mask = (
        (df["Home"] == squadra_home) &
        (df["Away"] == squadra_away)
    )
    df_match = df[mask]

    st.write(f"Partite trovate: {len(df_match)}")

    if len(df_match) > 0:

        # Correct Score Distribution
        st.subheader("Correct Score Distribution")
        df_match["Correct Score"] = df_match["Home Goal FT"].astype(str) + "-" + df_match["Away Goal FT"].astype(str)
        score_counts = df_match["Correct Score"].value_counts().reset_index()
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
        st.subheader("Over/Under FT")
        over_soglie = [0.5, 1.5, 2.5, 3.5, 4.5]
        over_data = []
        for soglia in over_soglie:
            perc = (df_match["Goals FT"] > soglia).mean() * 100
            over_data.append({"Over": f"Over {soglia}", "Percentage": perc})
        fig_over = px.bar(pd.DataFrame(over_data), x="Over", y="Percentage")
        st.plotly_chart(fig_over, use_container_width=True)

        # BTTS
        st.subheader("BTTS %")
        btts_pct = (df_match["BTTS"] == "Yes").mean() * 100
        st.metric("BTTS %", f"{btts_pct:.2f}%")

        # Time Frame Goals (Head-to-Head)
        st.subheader("⚽ Time Frame Goals (Head-to-Head)")

        home_goal_cols = [
            "home 1 goal segnato (min)",
            "home 2 goal segnato(min)",
            "home 3 goal segnato(min)",
            "home 4 goal segnato(min)",
            "home 5 goal segnato(min)",
            "home 6 goal segnato(min)",
            "home 7 goal segnato(min)",
            "home 8 goal segnato(min)",
            "home 9 goal segnato(min)"
        ]
        away_goal_cols = [
            "1  goal away (min)",
            "2  goal away (min)",
            "3 goal away (min)",
            "4  goal away (min)",
            "5  goal away (min)",
            "6  goal away (min)",
            "7  goal away (min)",
            "8  goal away (min)",
            "9  goal away (min)"
        ]

        goals_home = df_match[home_goal_cols].stack().dropna()
        goals_away = df_match[away_goal_cols].stack().dropna()

        bins = [0,15,30,45,60,75,90,120]
        labels = ["0-15","16-30","31-45","46-60","61-75","76-90","91+"]

        home_timeframe = pd.cut(goals_home, bins=bins, labels=labels, right=True)
        home_counts = home_timeframe.value_counts(normalize=True).sort_index() * 100

        away_timeframe = pd.cut(goals_away, bins=bins, labels=labels, right=True)
        away_counts = away_timeframe.value_counts(normalize=True).sort_index() * 100

        df_timeframe = pd.DataFrame({
            "Time Frame": labels,
            "Goals Home (%)": home_counts.reindex(labels).fillna(0).values,
            "Goals Away (%)": away_counts.reindex(labels).fillna(0).values
        })

        st.dataframe(df_timeframe)

        fig_time = px.bar(
            df_timeframe,
            x="Time Frame",
            y=["Goals Home (%)", "Goals Away (%)"],
            barmode="group",
            title="Distribuzione Time Frame Goals (Head-to-Head)"
        )
        st.plotly_chart(fig_time, use_container_width=True)

        # Head-to-Head dettaglio
        st.subheader("Head-to-Head Dettaglio")
        st.dataframe(
            df_match[[
                "Data", "Home", "Away",
                "Home Goal FT", "Away Goal FT"
            ]].sort_values("Data", ascending=False)
        )

    else:
        st.info("Nessuna partita trovata fra queste squadre.")
