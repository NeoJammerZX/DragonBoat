import streamlit as st
import pandas as pd
import html
import os
import base64
import io

# Helper: render an HTML table with centered cells and styled header
def render_table(rows, columns):
        """rows: list of dicts, columns: list of (key,label)"""
        if not rows:
                return ""
        # Build header and rows
        header_cells = "".join([f"<th style=\"text-align:center\">{html.escape(label)}</th>" for _, label in columns])
        body_rows = []
        for r in rows:
                cells = []
                for key, _ in columns:
                        val = r.get(key, "")
                        if isinstance(val, float):
                                cell = f"{val:.1f}"
                        else:
                                cell = str(val)
                        cells.append(f"<td>{html.escape(cell)}</td>")
                body_rows.append(f"<tr>{''.join(cells)}</tr>")
        body_html = "".join(body_rows)

        table_html = f"""
        <div style="display:flex; justify-content:center; width:100%;">
        <table style="width:80%; margin:0 auto; border-collapse:collapse; font-family:Arial,Helvetica,sans-serif;">
            <thead>
                <tr style="background: linear-gradient(to right,#172983,#009ee0);">
                    {header_cells}
                </tr>
            </thead>
            <tbody>
                {body_html}
            </tbody>
        </table>
        </div>
        <style>
            table th {{ color: white; font-weight:700; padding:8px; text-align:center; text-transform:capitalize; }}
            table td {{ padding:8px; text-align:center; border-bottom:1px solid #e6eef9; }}
            table tr:nth-child(even) {{ background:#fbfdff; }}
        </style>
        """
        return table_html


def render_visual_table(rows, side):
    """Render minimal rows with seat badge on the left and name/weight cells, no headers."""
    if not rows:
        return ""
    row_html = []
    for r in rows:
        seat = html.escape(str(r.get("Seat", "")))
        name = html.escape(str(r.get("Name", "")))
        weight = r.get("Weight", "")
        classification = (r.get("Classification", "") or "").lower()
        try:
            weight_str = f"{float(weight):.0f}"
        except Exception:
            weight_str = html.escape(str(weight))

        name_color = "#ff7eb9" if classification == "alpha" else "#8ec5ff"

        row_html.append(
            f"""
            <div style='display:flex; align-items:center; gap:8px; margin:4px 0;'>
                <div style='width:28px; text-align:center; background:#e8edf4; border-radius:6px; padding:6px 4px; font-weight:700; color:#2b3a4a;'>{seat}</div>
                <div style='flex:1; display:flex; align-items:center; justify-content:space-between; background:#ffffff; border:1px solid #d9e4f2; border-radius:10px; padding:8px 10px;'>
                    <span style='font-weight:700; color:{name_color};'>{name}</span>
                    <span style='font-weight:700; color:#2b3a4a;'>{weight_str}</span>
                </div>
            </div>
            """
        )

    return "".join(row_html)


def generate_seating_svg(bow_rows, stroke_rows, image_path, view_w=1000, view_h=1400):
    """Return an SVG string embedding the seating diagram image and overlaying seats up to 10 rows.
    bow_rows and stroke_rows are lists of dicts with keys 'Seat', 'Name', and 'Weight'.
    Layout mirrors the reference: Bow shows Name | Weight, Stroke shows Weight | Name.
    """
    max_rows = min(10, max(len(bow_rows), len(stroke_rows)))
    if max_rows == 0:
        return ""

    # Prepare image data URI if file exists
    img_href = None
    try:
        if image_path and os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                img_b = f.read()
            img_b64 = base64.b64encode(img_b).decode('ascii')
            mime = 'image/webp'
            img_href = f"data:{mime};base64,{img_b64}"
    except Exception:
        img_href = None

    left_x = int(view_w * 0.30)
    right_x = int(view_w * 0.70)
    mid_x = int(view_w * 0.50)
    top_margin = int(view_h * 0.08)
    bottom_margin = int(view_h * 0.08)
    usable_h = view_h - top_margin - bottom_margin
    gap = usable_h / max_rows if max_rows > 0 else 0

    def fmt_weight(val):
        try:
            v = float(val)
            return f"{v:.0f}"
        except Exception:
            return str(val) if val is not None else ""

    # Start SVG
    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w} {view_h}" width="100%" preserveAspectRatio="xMidYMid meet">')
    if img_href:
        svg_parts.append(f'<image href="{img_href}" x="0" y="0" width="{view_w}" height="{view_h}" preserveAspectRatio="xMidYMid meet" />')
    else:
        svg_parts.append(f'<rect x="0" y="0" width="{view_w}" height="{view_h}" fill="#ffffff" stroke="#cccccc"/>')

    # Seat rows
    for i in range(max_rows):
        y = top_margin + i * gap + int(gap / 2)
        seat_num = i + 1
        # Seat number near center
        svg_parts.append(f'<text x="{mid_x}" y="{int(y)+6}" font-family="Arial,Helvetica,sans-serif" font-size="22" font-weight="700" text-anchor="middle" fill="#222222">{seat_num}</text>')

        # Bow side block (Name | Weight)
        if i < len(bow_rows):
            name = html.escape(str(bow_rows[i].get('Name', '')))
            weight = html.escape(fmt_weight(bow_rows[i].get('Weight', '')))
            cls = (bow_rows[i].get('Classification', '') or '').lower()
            name_color = "#ff7eb9" if cls == "alpha" else "#8ec5ff"
            rect_x = left_x - 160
            rect_w = 200
            svg_parts.append(f'<rect x="{rect_x}" y="{int(y)-24}" rx="6" ry="6" width="{rect_w}" height="48" fill="#f5d0a9" stroke="#c89b63" stroke-width="1.5" opacity="0.95" />')
            svg_parts.append(f'<text x="{rect_x + 10}" y="{int(y)+8}" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="700" fill="{name_color}" text-anchor="start">{name}</text>')
            svg_parts.append(f'<text x="{rect_x + rect_w - 10}" y="{int(y)+8}" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="700" fill="#3b2d16" text-anchor="end">{weight}</text>')

        # Stroke side block (Weight | Name)
        if i < len(stroke_rows):
            name = html.escape(str(stroke_rows[i].get('Name', '')))
            weight = html.escape(fmt_weight(stroke_rows[i].get('Weight', '')))
            cls = (stroke_rows[i].get('Classification', '') or '').lower()
            name_color = "#ff7eb9" if cls == "alpha" else "#8ec5ff"
            rect_x = right_x - 40
            rect_w = 200
            svg_parts.append(f'<rect x="{rect_x}" y="{int(y)-24}" rx="6" ry="6" width="{rect_w}" height="48" fill="#d0e6f9" stroke="#7ea8d6" stroke-width="1.5" opacity="0.95" />')
            svg_parts.append(f'<text x="{rect_x + 16}" y="{int(y)+8}" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="700" fill="#1f3656" text-anchor="start">{weight}</text>')
            svg_parts.append(f'<text x="{rect_x + rect_w - 10}" y="{int(y)+8}" font-family="Arial,Helvetica,sans-serif" font-size="18" font-weight="700" fill="{name_color}" text-anchor="end">{name}</text>')

    svg_parts.append('</svg>')
    svg = ''.join(svg_parts)
    return f'<div style="display:flex; justify-content:center;">{svg}</div>'


def compute_balance_metrics(assign_rows):
    """Compute weight totals and balance deltas for a seating assignment."""
    if not assign_rows:
        return {}
    left = sum(float(r.get('Weight') or 0) for r in assign_rows if (r.get('Side') or '').lower() == 'bow')
    right = sum(float(r.get('Weight') or 0) for r in assign_rows if (r.get('Side') or '').lower() == 'stroke')
    front = sum(float(r.get('Weight') or 0) for r in assign_rows if (r.get('Seat') or 0) and int(r.get('Seat')) <= 5)
    back = sum(float(r.get('Weight') or 0) for r in assign_rows if (r.get('Seat') or 0) and int(r.get('Seat')) > 5)
    total = left + right
    diff_lr = left - right
    diff_fb = front - back
    return {
        "left": left,
        "right": right,
        "front": front,
        "back": back,
        "total": total,
        "diff_lr": diff_lr,
        "diff_fb": diff_fb,
    }


def render_balance_cross(diff_lr, diff_fb, total_weight):
    """Render a simple cross (front/back, left/right) with a dot representing balance."""
    # Normalize to -1..1 based on 1/4 of total weight to avoid huge offsets
    scale = max(total_weight, 1)
    norm_x = max(-1.0, min(1.0, diff_lr / (scale / 4)))
    norm_y = max(-1.0, min(1.0, diff_fb / (scale / 4)))
    size = 160
    center = size / 2
    radius = 8
    dot_x = center + norm_x * (center - 24)
    dot_y = center - norm_y * (center - 24)
    svg = f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
        <line x1="{center}" y1="16" x2="{center}" y2="{size-16}" stroke="#666" stroke-width="2" />
        <line x1="16" y1="{center}" x2="{size-16}" y2="{center}" stroke="#666" stroke-width="2" />
        <circle cx="{dot_x}" cy="{dot_y}" r="{radius}" fill="#009ee0" stroke="#003f87" stroke-width="2" />
        <text x="{center}" y="12" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="12" fill="#444">front</text>
        <text x="{center}" y="{size-4}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="12" fill="#444">back</text>
        <text x="12" y="{center+4}" text-anchor="start" font-family="Arial,Helvetica,sans-serif" font-size="12" fill="#444">left</text>
        <text x="{size-12}" y="{center+4}" text-anchor="end" font-family="Arial,Helvetica,sans-serif" font-size="12" fill="#444">right</text>
    </svg>
    """
    return svg


def distribute_others_by_weight(bow_list, stroke_list, others):
    """Place no-preference paddlers to the lighter side by weight."""
    def total_w(lst):
        return sum(float(m.get('weight') or 0) for m in lst)

    for o in sorted(others, key=lambda m: float(m.get('weight') or 0), reverse=True):
        if total_w(bow_list) <= total_w(stroke_list):
            bow_list.append(o)
        else:
            stroke_list.append(o)
    return bow_list, stroke_list


def build_side_with_roles(members):
    """Arrange up to 10 seats honoring roles: Pacers front (1-2), Rockets back (9-10)."""
    pacers = sorted([m for m in members if (m.get('role') or '').lower() == 'pacer'], key=lambda m: float(m.get('weight') or 0), reverse=True)
    rockets = sorted([m for m in members if (m.get('role') or '').lower() == 'rocket'], key=lambda m: float(m.get('weight') or 0), reverse=True)
    engines = sorted([m for m in members if (m.get('role') or '').lower() not in ('pacer', 'rocket')], key=lambda m: float(m.get('weight') or 0), reverse=True)

    seats = [None] * 10

    def pop_heaviest(groups):
        for g in groups:
            if g:
                return g.pop(0)
        return None

    # Front seats prefer pacers
    for idx in range(2):
        seats[idx] = pop_heaviest([pacers, engines, rockets])

    # Back seats prefer rockets
    for idx in [9, 8]:
        seats[idx] = pop_heaviest([rockets, engines, pacers])

    # Middle seats with remaining weight (engines first)
    for idx in range(2, 8):
        seats[idx] = pop_heaviest([engines, pacers, rockets])

    # Remove Nones and keep order
    return [s for s in seats if s is not None]


def dicts_to_csv_bytes(rows, fieldnames=None):
    """Convert a list of dicts to CSV bytes. If fieldnames provided, order/select columns accordingly."""
    if not rows:
        return "".encode('utf-8')
    df = pd.DataFrame(rows)
    if fieldnames:
        cols = [c for c in fieldnames if c in df.columns]
        if cols:
            df = df[cols]
    return df.to_csv(index=False).encode('utf-8')


def import_roster_from_csv_bytes(csv_bytes):
    """Parse CSV bytes into a list of roster dicts with keys matching the app.
    Accepts columns: name, weight, level, position, classification (case-insensitive).
    """
    if not csv_bytes:
        return []
    try:
        bio = io.BytesIO(csv_bytes)
        df = pd.read_csv(bio)
    except Exception:
        # try reading as text
        try:
            s = csv_bytes.decode('utf-8') if isinstance(csv_bytes, (bytes, bytearray)) else str(csv_bytes)
            df = pd.read_csv(io.StringIO(s))
        except Exception:
            return []

    # Normalize column names
    df_cols = {c.lower(): c for c in df.columns}
    mapping = {}
    for key in ['name', 'weight', 'level', 'position', 'classification', 'role']:
        if key in df_cols:
            mapping[key] = df_cols[key]

    rows = []
    for _, r in df.iterrows():
        entry = {}
        entry['name'] = str(r.get(mapping.get('name', ''), '')).strip()
        # weight: attempt numeric
        try:
            w = r.get(mapping.get('weight', ''), '')
            entry['weight'] = float(w) if w != '' and not pd.isna(w) else 0.0
        except Exception:
            entry['weight'] = 0.0
        entry['level'] = str(r.get(mapping.get('level', ''), '')).strip()
        entry['position'] = str(r.get(mapping.get('position', ''), '')).strip()
        entry['classification'] = str(r.get(mapping.get('classification', ''), '')).strip()
        entry['role'] = str(r.get(mapping.get('role', ''), '')).strip()
        if entry['name']:
            rows.append(entry)
    return rows


def sort_roster(rows, method):
    """Return a new list sorted according to method string."""
    if not rows:
        return []
    method = method or "None"
    if method == "None":
        return list(rows)
    if method == "Name (A→Z)":
        return sorted(rows, key=lambda r: (r.get('name') or '').lower())
    if method == "Name (Z→A)":
        return sorted(rows, key=lambda r: (r.get('name') or '').lower(), reverse=True)
    if method == "Weight (Light→Heavy)":
        return sorted(rows, key=lambda r: float(r.get('weight') or 0.0))
    if method == "Weight (Heavy→Light)":
        return sorted(rows, key=lambda r: float(r.get('weight') or 0.0), reverse=True)
    if method == "Level (A→D)":
        order = {"A": 0, "B": 1, "C": 2, "D": 3}
        return sorted(rows, key=lambda r: order.get((r.get('level') or '').upper(), 99))
    if method == "Level (D→A)":
        order = {"A": 0, "B": 1, "C": 2, "D": 3}
        return sorted(rows, key=lambda r: order.get((r.get('level') or '').upper(), 99), reverse=True)
    if method == "Alpha/Bravo (Alpha first)":
        order = {"Alpha": 0, "Bravo": 1}
        return sorted(rows, key=lambda r: order.get((r.get('classification') or ''), 99))
    if method == "Alpha/Bravo (Bravo first)":
        order = {"Alpha": 0, "Bravo": 1}
        return sorted(rows, key=lambda r: order.get((r.get('classification') or ''), 99), reverse=True)
    # default fallback
    return list(rows)

# Simple Dragonboat Seating app (cleaned)

# Sidebar style
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(to top, #172983, #009ee0);
        color: white !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    [data-testid="stSidebar"] label { color: white !important; }
    /* Center main app headings */
    div[data-testid="stAppViewContainer"] h1, div[data-testid="stAppViewContainer"] h2, div[data-testid="stAppViewContainer"] h3 {
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display custom sidebar logo with text (FF7-themed)
try:
    with open(r"https://github.com/NeoJammerZX/DragonBoat/blob/main/FBALogo2.png", 'rb') as f:
        logo_b64 = base64.b64encode(f.read()).decode('ascii')
    logo_data_uri = f"data:image/png;base64,{logo_b64}"
    st.sidebar.markdown(
        f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; padding:16px; background:linear-gradient(135deg, #bacdf5 0%, #013b25 100%); border-radius:10px; margin-bottom:16px; border:2px solid #ffd86b;">
            <img src="{logo_data_uri}" style="width:70px; height:70px; object-fit:contain;">
            <div style="color:#ffd86b; font-size:16px; font-weight:800; text-align:center; text-transform:uppercase; letter-spacing:1px;">Firebase Alpha<br>Dragon Boat Team</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
except Exception:
    st.sidebar.markdown(
        """
        <div style="text-align:center; color:#ffd86b; font-size:16px; font-weight:800; padding:16px; background:linear-gradient(135deg, #bacdf5 0%, #013b25 100%); border-radius:10px; border:2px solid #ffd86b;">Firebase Alpha Dragon Boat Team</div>
        """,
        unsafe_allow_html=True,
    )

# Display image logo
try:
    # Place the image in the middle column so it appears centered at the top
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(r"https://github.com/NeoJammerZX/DragonBoat/blob/main/FBALogo2.png", width=300, use_container_width=False)
        st.markdown("[Firebase Alpha Dragonboat Facebook Page](https://www.facebook.com/firebasealphadragonboat)")
except Exception:
    # Fallback: centered markdown link
    st.markdown('<div style="text-align:center">[Firebase Alpha Dragonboat Facebook Page](https://www.facebook.com/firebasealphadragonboat)</div>', unsafe_allow_html=True)

# Navigation: only Dragonboat Seating
st.sidebar.title("Navigation")
st.session_state.page = st.sidebar.radio("Go to:", ["Dragonboat Seating Calculator"])  # single page for now

# Sidebar image (centered in sidebar)
try:
    sc1, sc2, sc3 = st.sidebar.columns([1, 2, 1])
    with sc2:
        st.image(
            r"https://github.com/NeoJammerZX/DragonBoat/blob/main/DragonBoatSeating.webp",
            #caption="Dragon Boat seating helper - input crew and assign seats",
            width=150,
            use_container_width=False,
        )
except Exception:
    # Fallback: render a centered markdown link if image can't be displayed in sidebar
    st.sidebar.markdown('<div style="text-align:center">[Dragon Boat seating helper]</div>', unsafe_allow_html=True)

# Sidebar Dashboard: show a centered, styled summary only when on the Dragonboat Seating page
if st.session_state.page == "Dragonboat Seating Calculator":
        members = st.session_state.get('dragon_members', [])
        total = len(members)
        bow_count = sum(1 for m in members if (m.get('position') or '').lower() == 'bow')
        stroke_count = sum(1 for m in members if (m.get('position') or '').lower() == 'stroke')
        alpha_count = sum(1 for m in members if (m.get('classification') or '').lower() == 'alpha')
        bravo_count = sum(1 for m in members if (m.get('classification') or '').lower() == 'bravo')

        dashboard_html = f"""
<div style="padding:10px; border-radius:10px; background: linear-gradient(135deg,#172983 0%, #009ee0 100%); color: white; font-family:Arial,Helvetica,sans-serif; text-align:center;">
    <div style="font-weight:700; font-size:18px; margin-bottom:8px;">Dashboard</div>
    <div style="display:flex; justify-content:space-between; gap:8px;">
        <div style="flex:1; background:rgba(255,255,255,0.06); padding:8px; border-radius:8px;">
            <div style="font-size:12px; opacity:0.9;">Stroke</div>
            <div style="font-size:20px; font-weight:800; color:#ffd86b;">{stroke_count}</div>
        </div>
        <div style="flex:1; background:rgba(255,255,255,0.06); padding:8px; border-radius:8px;">
            <div style="font-size:12px; opacity:0.9;">Bow</div>
            <div style="font-size:20px; font-weight:800; color:#ffd86b;">{bow_count}</div>
        </div>
    </div>
    <div style="height:8px"></div>
    <div style="display:flex; justify-content:space-between; gap:8px;">
        <div style="flex:1; background:rgba(255,255,255,0.06); padding:8px; border-radius:8px;">
            <div style="font-size:12px; opacity:0.9;">Alpha</div>
            <div style="font-size:20px; font-weight:800; color:#ffd86b;">{alpha_count}</div>
        </div>
        <div style="flex:1; background:rgba(255,255,255,0.06); padding:8px; border-radius:8px;">
            <div style="font-size:12px; opacity:0.9;">Bravo</div>
            <div style="font-size:20px; font-weight:800; color:#ffd86b;">{bravo_count}</div>
        </div>
    </div>
    <div style="height:8px"></div>
    <div style="background:rgba(0,0,0,0.12); padding:8px; border-radius:8px; margin-top:6px;">
        <div style="font-size:12px; opacity:0.9;">Total</div>
        <div style="font-size:20px; font-weight:800; color:#ffd86b;">{total}</div>
    </div>
</div>
"""
        st.sidebar.markdown(dashboard_html, unsafe_allow_html=True)


# Ensure session state containers exist
if 'dragon_members' not in st.session_state:
    st.session_state.dragon_members = []
if 'dragon_assignment' not in st.session_state:
    st.session_state.dragon_assignment = []
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

# Dragonboat Seating Page
if st.session_state.page == "Dragonboat Seating Calculator":
    st.title("Dragonboat Seating")

    st.markdown(
        """
        <hr style="margin:10px 0; border:none; border-top:10px; background: linear-gradient(to right,#172983,#009ee0); height:10px;" />
        """,
        unsafe_allow_html=True,
    )
    
    # Level descriptions
    level_desc = {
        "A": "Active, attends training regularly, fit, experienced",
        "B": "In between A and C, good attendance and training, developing strength and consistency",
        "C": "Not attending regularly, less experience, learning technique and building fitness",
        "D": "Newbie — limited experience, not attending regularly yet",
    }
    st.markdown(
        """
        **Input name of paddler and their details below:**
        """
    )

    # Input form
    # Position mapping (remember: Bow = left, Stroke = right)
    POSITION_TO_SIDE = {"Bow": "Bow", "Stroke": "Stroke"}
    # Classification mapping (Alpha = female, Bravo = male)
    CLASS_TO_GENDER = {"Alpha": "Female", "Bravo": "Male"}

    with st.form(key='add_member_form', clear_on_submit=True):
        name = st.text_input("Name")
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5, format="%.1f")
        level = st.selectbox(
            "Level",
            list(level_desc.keys()),
            format_func=lambda k: f"{k} — {level_desc[k]}",
        )
        position = st.selectbox("Preferred Position Side", ("Bow", "Stroke"), help="Bow = left (Port); Stroke = right (Starboard)")
        classification = st.selectbox("Alpha/Bravo", ("Alpha", "Bravo"), help="Alpha = female, Bravo = male")
        role = st.selectbox("Role", ("Pacer", "Engine", "Rocket"), help="Pacer: front seats (1-2), Engine: middle power, Rocket: back power")
        submitted = st.form_submit_button("Add Member")
        if submitted:
            if not name:
                st.warning("Please enter a name.")
            else:
                st.session_state.dragon_members.append({"name": name, "weight": float(weight), "level": level, "position": position, "classification": classification, "role": role})
                st.success(f"Added {name}")

    st.subheader("Crew Roster")
    # Sorting filter for roster display
    sort_options = [
        "None",
        "Name (A→Z)",
        "Level (A→D)",
        "Level (D→A)",
        "Alpha/Bravo (Alpha first)",
        "Alpha/Bravo (Bravo first)",
        "Weight (Light→Heavy)",
        "Weight (Heavy→Light)",
    ]
    sort_choice = st.selectbox("Sort roster by", sort_options, index=0)

    displayed_rows = sort_roster(st.session_state.dragon_members, sort_choice)

    if displayed_rows:
        # Render a prettier HTML table and center it on the page
        cols = [("name", "Name"), ("weight", "Weight"), ("level", "Level"), ("classification", "Alpha/Bravo"), ("position", "Side"), ("role", "Role")]
        table_html = render_table(displayed_rows, cols)
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("No crew members yet. Add members using the form above or by importing an existing list below.")

    # Add a bit of vertical space between table and buttons
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Center the Clear Roster and Export Roster buttons below the roster
    cb_left, cb_mid, cb_right = st.columns([1,2,1])
    with cb_mid:
        bcol, dcol = st.columns([1,1])
        with bcol:
            if st.button("Clear Roster"):
                st.session_state.dragon_members = []
                st.session_state.dragon_assignment = []
                st.rerun()
        with dcol:
            roster_csv = dicts_to_csv_bytes(
                displayed_rows,
                fieldnames=["name", "weight", "level", "position", "classification", "role"],
            )
            if roster_csv:
                st.download_button("Export Roster CSV", data=roster_csv, file_name="dragon_roster.csv", mime="text/csv")
            else:
                st.button("Export Roster CSV", disabled=True)

# Import roster (centered uploader)
    ul_left, ul_mid, ul_right = st.columns([1,2,1])
    with ul_mid:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        uploaded = st.file_uploader("Import Roster CSV", type=["csv"], key="uploader")
        st.markdown('</div>', unsafe_allow_html=True)
        if uploaded is not None:
            # Center the import button
            ib_left, ib_mid, ib_right = st.columns([1, 2, 1])
            with ib_mid:
                if st.button("Import CSV to Roster", use_container_width=True):
                    try:
                        data = uploaded.read()
                        new_rows = import_roster_from_csv_bytes(data)
                        if new_rows:
                            # append imported members
                            st.session_state.dragon_members.extend(new_rows)
                            st.session_state.last_uploaded_file = uploaded.name
                            st.success(f"Imported {len(new_rows)} crew members from CSV")
                            st.rerun()
                        else:
                            st.warning("No valid rows found in uploaded CSV.")
                    except Exception as e:
                        st.error(f"Failed to import CSV: {e}")

    # Seating assignment (assign by Bow/Stroke preference and show visual)
    st.markdown("---")
    if st.session_state.dragon_members:
        # Center the Assign Seating button
        as_left, as_mid, as_right = st.columns([1, 2, 1])
        with as_mid:
            assign_btn = st.button("Assign Seating", use_container_width=True)
        if assign_btn:
            members = st.session_state.dragon_members.copy()
            # Separate by position preference
            bow_members = [m for m in members if (m.get('position') or '').lower() == 'bow']
            stroke_members = [m for m in members if (m.get('position') or '').lower() == 'stroke']
            others = [m for m in members if (m.get('position') or '').lower() not in ('bow', 'stroke')]

            # Distribute no-preference paddlers to the lighter side (by weight)
            bow_members, stroke_members = distribute_others_by_weight(bow_members, stroke_members, others)

            # Build per-side ordering with role rules (Pacers front, Rockets back), capped to 10 seats
            bow = build_side_with_roles(bow_members)
            stroke = build_side_with_roles(stroke_members)

            if len(bow_members) > 10 or len(stroke_members) > 10:
                st.info("Showing first 10 seats per side (extra paddlers were not seated).")

            max_rows = min(10, max(len(bow), len(stroke)))
            assign_rows = []
            # Build per-side seat rows (pair by row number)
            for row in range(max_rows):
                if row < len(bow):
                    m = bow[row]
                    assign_rows.append({"Seat": row + 1, "Side": "Bow", "Name": m.get('name'), "Weight": m.get('weight'), "Level": m.get('level'), "Classification": m.get('classification', ''), "Role": m.get('role', '')})
                if row < len(stroke):
                    m = stroke[row]
                    assign_rows.append({"Seat": row + 1, "Side": "Stroke", "Name": m.get('name'), "Weight": m.get('weight'), "Level": m.get('level'), "Classification": m.get('classification', ''), "Role": m.get('role', '')})

            st.session_state.dragon_assignment = assign_rows
            st.success("Seating assigned by Bow/Stroke preference.")

            # Visual seating layout: left column = Bow, center = boat diagram, right = Stroke
            st.markdown("### Visual Seating")
            left_col, img_col, right_col = st.columns([2, 4, 2])

            # Prepare simple row lists for left and right to display alongside the diagram
            left_rows = []
            right_rows = []
            for i in range(max_rows):
                left_name = bow[i].get('name') if i < len(bow) else ""
                left_w = bow[i].get('weight') if i < len(bow) else ""
                left_c = bow[i].get('classification') if i < len(bow) else ""
                right_name = stroke[i].get('name') if i < len(stroke) else ""
                right_w = stroke[i].get('weight') if i < len(stroke) else ""
                right_c = stroke[i].get('classification') if i < len(stroke) else ""
                left_rows.append({"Seat": i + 1, "Name": left_name, "Weight": left_w, "Classification": left_c})
                right_rows.append({"Seat": i + 1, "Weight": right_w, "Name": right_name, "Classification": right_c})

            # Display left list
            with left_col:
                st.markdown('<div style="text-align:center; font-weight:bold;">Bow</div>', unsafe_allow_html=True)
                left_html = render_visual_table(left_rows, side="bow")
                st.markdown(left_html, unsafe_allow_html=True)

            # Display diagram in the center
            with img_col:
                try:
                        svg = generate_seating_svg(left_rows, right_rows, r"https://github.com/NeoJammerZX/DragonBoat/blob/main/DragonBoatSeating.webp")
                        if svg:
                            st.markdown(svg, unsafe_allow_html=True)
                        else:
                            # fallback to plain image if SVG generation failed
                            st.image(r"https://github.com/NeoJammerZX/DragonBoat/blob/main/DragonBoatSeating.webp", use_column_width=True)
                except Exception:
                        st.info("Seating diagram or overlay could not be rendered.")

            # Display right list
            with right_col:
                st.markdown('<div style="text-align:center; font-weight:bold;">Stroke</div>', unsafe_allow_html=True)
                right_html = render_visual_table(right_rows, side="stroke")
                st.markdown(right_html, unsafe_allow_html=True)

            # Weight balance summary
            metrics = compute_balance_metrics(assign_rows)
            if metrics:
                diff_lr = metrics["diff_lr"]
                diff_fb = metrics["diff_fb"]
                summary_html = f"""
                <div style="margin-top:12px; display:flex; flex-wrap:wrap; gap:12px;">
                    <div style="flex:1; min-width:200px; padding:12px; border-radius:10px; background:linear-gradient(135deg,#172983,#009ee0); color:white;">
                        <div style="font-weight:700; font-size:16px; margin-bottom:8px;">Weight Totals</div>
                        <div>Left/Bow: <b>{metrics['left']:.1f} kg</b></div>
                        <div>Right/Stroke: <b>{metrics['right']:.1f} kg</b></div>
                        <div>Front (seats 1-5): <b>{metrics['front']:.1f} kg</b></div>
                        <div>Back (seats 6-10): <b>{metrics['back']:.1f} kg</b></div>
                        <div>Total: <b>{metrics['total']:.1f} kg</b></div>
                    </div>
                    <div style="flex:1; min-width:200px; padding:12px; border-radius:10px; background:#f7f9fc; border:1px solid #d9e4f2; color:#1f2d3d;">
                        <div style="font-weight:700; font-size:16px; margin-bottom:8px;">Balance Deltas</div>
                        <div>L/R (left - right): <b>{diff_lr:.1f} kg</b></div>
                        <div>Front/Back (front - back): <b>{diff_fb:.1f} kg</b></div>
                        <div>Target: aim for values near 0</div>
                    </div>
                    <div style="flex:1; min-width:180px; padding:12px; border-radius:10px; background:#ffffff; border:1px solid #d0d8e0; display:flex; align-items:center; justify-content:center;">
                        {render_balance_cross(diff_lr, diff_fb, metrics['total'])}
                    </div>
                </div>
                """
                st.markdown(summary_html, unsafe_allow_html=True)

                # Suggestions
                suggestions = []
                bow_assign = [r for r in assign_rows if (r.get('Side') or '').lower() == 'bow']
                stroke_assign = [r for r in assign_rows if (r.get('Side') or '').lower() == 'stroke']
                if abs(diff_lr) > 5 and bow_assign and stroke_assign:
                    if diff_lr > 0:
                        heavy_side = bow_assign
                        light_side = stroke_assign
                        heavy_label = "Bow"
                        light_label = "Stroke"
                    else:
                        heavy_side = stroke_assign
                        light_side = bow_assign
                        heavy_label = "Stroke"
                        light_label = "Bow"
                    heavy_p = max(heavy_side, key=lambda r: float(r.get('Weight') or 0))
                    light_p = min(light_side, key=lambda r: float(r.get('Weight') or 0))
                    suggestions.append(f"Swap heavier {heavy_label} paddler {heavy_p.get('Name','')} ({heavy_p.get('Weight','')} kg) with lighter {light_label} paddler {light_p.get('Name','')} ({light_p.get('Weight','')} kg) to reduce L/R delta.")

                if abs(diff_fb) > 5:
                    if diff_fb > 0:
                        suggestions.append("Front is heavier; move one mid/front paddler toward seats 7-10.")
                    else:
                        suggestions.append("Back is heavier; move one back paddler toward seats 1-4.")

                if not suggestions:
                    suggestions.append("Setup already close to balanced; minor tweaks only if crew preference allows.")

                st.markdown("**Balance Suggestions**")
                for s in suggestions:
                    st.markdown(f"- {s}")

    # Show assignment
    if st.session_state.dragon_assignment:
        st.subheader("Seating Assignment")
        # Ensure consistent column order for assignment
        cols = [("Seat", "Seat"), ("Side", "Side"), ("Name", "Name"), ("Weight", "Weight"), ("Level", "Level"), ("Classification", "Alpha/Bravo"), ("Role", "Role")]
        # Convert session assignment rows (dicts) to uniform dicts with lowercase keys mapping
        rows = []
        for r in st.session_state.dragon_assignment:
            # r may already have capitalized keys
            normalized = {k if k in [c[0] for c in cols] else k: v for k, v in r.items()}
            # Ensure classification and role fields present (if member data included it)
            if "Classification" not in normalized and isinstance(normalized.get("Name"), str):
                # try to find member by name and pull classification and role
                name = normalized.get("Name")
                for m in st.session_state.dragon_members:
                    if m.get("name") == name:
                        if "classification" in m:
                            normalized["Classification"] = m.get("classification")
                        if "role" in m:
                            normalized["Role"] = m.get("role")
                        break
            rows.append(normalized)
        # render_table expects keys as used in cols; table will use the provided labels
        table_html = render_table(rows, cols)
        st.markdown(table_html, unsafe_allow_html=True)

        # Add centered download button for the assignment CSV
        ab_left, ab_mid, ab_right = st.columns([1,2,1])
        with ab_mid:
            assign_csv = dicts_to_csv_bytes(
                st.session_state.dragon_assignment,
                fieldnames=["Seat", "Side", "Name", "Weight", "Level", "Classification", "Role"],
            )
            if assign_csv:
                st.download_button("Export Assignment CSV", data=assign_csv, file_name="dragon_assignment.csv", mime="text/csv")
            else:
                st.button("Export Assignment CSV", disabled=True)

    st.markdown("\n\n")
        # End of DragonBoat Seating app


