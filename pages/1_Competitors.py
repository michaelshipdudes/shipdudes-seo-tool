"""
pages/1_Competitors.py
Manage the list of competitor blog URLs — add, remove, and save without
touching any config files.
"""

import streamlit as st
from utils import load_settings, save_settings, render_sidebar, get_global_css

st.set_page_config(
    page_title="Competitors - ShipDudes",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(get_global_css(), unsafe_allow_html=True)
render_sidebar()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Competitors")
st.caption(
    "The blogs listed here are scraped during Run Analysis. "
    "Changes are saved immediately to settings.json."
)

settings    = load_settings()
competitors = settings.get("competitors", [])

# ---------------------------------------------------------------------------
# Current competitors table
# ---------------------------------------------------------------------------
st.subheader(f"Tracked Blogs ({len(competitors)})")

if not competitors:
    st.info("No competitors configured yet. Add one below.")
else:
    # Column headers
    h1, h2, h3, h4 = st.columns([2, 5, 1, 1])
    h1.markdown("**Company**")
    h2.markdown("**Blog URL**")
    h3.markdown("")
    h4.markdown("")
    st.divider()

    for idx, comp in enumerate(competitors):
        col_name, col_url, col_link, col_del = st.columns([2, 5, 1, 1])

        with col_name:
            st.write(comp.get("name", "—"))
        with col_url:
            st.write(comp.get("url", "—"))
        with col_link:
            st.link_button("Visit", comp.get("url", "#"), use_container_width=True)
        with col_del:
            if st.button("Remove", key=f"del_{idx}", use_container_width=True):
                competitors.pop(idx)
                settings["competitors"] = competitors
                save_settings(settings)
                st.toast(f"Removed {comp.get('name', 'competitor')}", icon="🗑️")
                st.rerun()

# ---------------------------------------------------------------------------
# Add new competitor
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Add Competitor")

with st.form("add_competitor_form", clear_on_submit=True):
    col_a, col_b, col_c = st.columns([2, 5, 1])
    with col_a:
        new_name = st.text_input("Company Name", placeholder="e.g. Shipwire")
    with col_b:
        new_url  = st.text_input("Blog Index URL", placeholder="https://www.shipwire.com/blog/")
    with col_c:
        st.markdown("<div style='padding-top:1.75rem;'>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Add", use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if not new_name or not new_url:
            st.error("Both Company Name and Blog URL are required.")
        elif not new_url.startswith("http"):
            st.error("URL must start with http:// or https://")
        elif any(c["url"] == new_url for c in competitors):
            st.warning(f"{new_url} is already in the list.")
        else:
            competitors.append({"name": new_name.strip(), "url": new_url.strip()})
            settings["competitors"] = competitors
            save_settings(settings)
            st.success(f"Added **{new_name}** — run a new analysis to include it.")
            st.rerun()

# ---------------------------------------------------------------------------
# Reset to defaults
# ---------------------------------------------------------------------------
st.divider()
with st.expander("Reset to defaults"):
    st.caption(
        "This will replace your current competitor list with the original "
        "six pre-loaded competitors from config.py."
    )
    if st.button("Reset to default competitors", type="secondary"):
        from config import COMPETITOR_BLOGS
        settings["competitors"] = COMPETITOR_BLOGS
        save_settings(settings)
        st.success("Competitor list reset to defaults.")
        st.rerun()
