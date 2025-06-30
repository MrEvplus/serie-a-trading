import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

st.title("⚽ Serie A Trading Dashboard")

# Carica file dati
uploaded_file = st.file_uploader("Carica file Excel o CSV", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    # Caricamento dati
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, sheet_name=None)
        # Assumiamo ci sia un solo foglio
        df = list(df.values())[0]
    
    st.success("File caricato con successo!")

    # Prepariamo i dati
    df["datameci"] = pd.to_datetime(df["datameci"], errors='coerce')

    # Calcola esito finale
    df["esito"] = np.where(
        df["scor1"] > df["scor2"], "Win",
        np.where(df["scor1"] == df["scor2"], "Draw", "Lose")
    )

    # Calcola gol totali
    df["goals_ft"] = df["scor1"] + df["scor2"]
    df["goals_1t"] = df["scorp1"] + df["scorp2"]
    df["goals_2t"] = df["goals_ft"] - df["goals_1t"]

    # BTTS
    df["btts"] = np.where(
        (df["scor1"] > 0) & (df["scor2"] > 0),
        "Yes", "No"
    )

    # Squadre uniche
    squadre = pd.unique(df["txtechipa1"].tolist() + df["txtechipa2"].tolist())
    squadra_sel = st.selectbox("Scegli la squadra:", sorted(squadre))

    # Home o Away
    side = st.radio("Partite in casa o trasferta?", ["Home", "Away"])

    # Range quote
    quota_ranges = {
        "1.01-1.49": (1.01, 1.49),
        "1.50-1.99": (1.50, 1.99),
        "2.00-3.00": (2.00, 3.00)
    }
    quota_sel = st.multiselect(
        "Seleziona range quota:",
        list(quota_ranges.keys()),
        default=list(quota_ranges.keys())
    )

    # Filtriamo il DataFrame
    if side == "Home":
        df_team = df[df["txtechipa1"] == squadra_sel]
        df_team["quota"] = df_team["cotaa"]
    else:
        df_team = df[df["txtechipa2"] == squadra_sel]
        df_team["quota"] = df_team["cotad"]

    # Applichiamo filtri quota
    quota_masks = []
    for q in quota_sel:
        min_q, max_q = quota_ranges[q]
        quota_masks.append(
            (df_team["quota"] >= min_q) & (df_team["quota"] <= max_q)
        )
    if quota_masks:
        mask_finale = quota_masks[0]
        for m in quota_masks[1:]:
            mask_finale |= m
        df_team = df_team[mask_finale]

    st.write(f"Partite trovate: {len(df_team)}")

    if len(df_team) > 0:
        # ROI Back
        df_team["back_profit"] = np.where(
            df_team["esito"] == "Win",
            (df_team["quota"] - 1) * 10,
            -10
        )
        roi_back = round(df_team["back_profit"].sum() / (10 * len(df_team)) * 100, 2)

        # ROI Lay
        df_team["lay_profit"] = np.where(
            df_team["esito"] != "Win",
            10,
            -(df_team["quota"] - 1) * 10
        )
        roi_lay = round(df_team["lay_profit"].sum() / (10 * len(df_team)) * 100, 2)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("ROI Back", f"{roi_back} %")
        with col2:
            st.metric("ROI Lay", f"{roi_lay} %")

        # Win/Draw/Lose %
        esiti_counts = df_team["esito"].value_counts(normalize=True) * 100
        fig_pie = px.pie(
            names=esiti_counts.index,
            values=esiti_counts.values,
            title="Match Result Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # BTTS %
        btts_counts = df_team["btts"].value_counts(normalize=True) * 100
        fig_btts = px.pie(
            names=btts_counts.index,
            values=btts_counts.values,
            title="BTTS Distribution",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_btts, use_container_width=True)

        # AVG GOALS
        avg_ft = df_team["goals_ft"].mean()
        avg_1t = df_team["goals_1t"].mean()
        avg_2t = df_team["goals_2t"].mean()

        st.write(f"**Average goals FT:** {avg_ft:.2f}")
        st.write(f"**Average goals 1st Half:** {avg_1t:.2f}")
        st.write(f"**Average goals 2nd Half:** {avg_2t:.2f}")

        # Segna almeno 1 goal %
        if side == "Home":
            segna = (df_team["scor1"] > 0).mean() * 100
        else:
            segna = (df_team["scor2"] > 0).mean() * 100
        st.write(f"**{squadra_sel} segna almeno un gol → {segna:.2f} %**")

        # Over %
        soglie = [0.5, 1.5, 2.5, 3.5, 4.5]
        st.write("### Over % - First Half")
        for soglia in soglie:
            perc = (df_team["goals_1t"] > soglia).mean() * 100
            st.write(f"Over {soglia} → {perc:.2f} %")

        st.write("### Over % - Second Half")
        for soglia in soglie:
            perc = (df_team["goals_2t"] > soglia).mean() * 100
            st.write(f"Over {soglia} → {perc:.2f} %")

        st.write("### Over % - Full Time")
        for soglia in soglie:
            perc = (df_team["goals_ft"] > soglia).mean() * 100
            st.write(f"Over {soglia} → {perc:.2f} %")

        # Tabella dettagli
        st.dataframe(
            df_team[
                ["datameci", "txtechipa1", "txtechipa2", "quota", "scor1", "scor2", "esito"]
            ].sort_values("datameci", ascending=False)
        )

else:
    st.info("Carica un file per iniziare.")

