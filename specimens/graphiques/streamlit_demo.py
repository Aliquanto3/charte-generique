"""Appli témoin du thème Streamlit de la charte (`dist/streamlit-sombre.toml`). Lancée par `rendre.py`."""
import streamlit as st

st.title("Charte générique")
st.write("Texte courant, avec un [lien](https://example.org) et du `code en ligne`.")
c1, c2 = st.columns(2)
c1.button("Action principale", type="primary")
c2.button("Action secondaire")
st.bar_chart({"Série 1": [3, 5, 2, 6], "Série 2": [4, 2, 5, 3], "Série 3": [2, 6, 3, 4], "Série 4": [5, 3, 6, 2]})
st.text_input("Champ de saisie", "Valeur")
st.success("Message de réussite")
