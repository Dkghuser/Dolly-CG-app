import streamlit as st
from fpdf import FPDF
from PIL import Image
import matplotlib.pyplot as plt
import tempfile
import os
import datetime

# --- PAGE CONFIGURATION (Must be the first command) ---
st.set_page_config(page_title="Dolly Dynamic CG & Risk Evaluation", 
                   layout="wide", 
                   #initial_sidebar_state="expanded"
                  )

# --- Hide streamlit header, footer & github icon ---
# hide_streamlit_style = """
#    <style>
#    #MainMenu {visibility: hidden;}
#    footer {visibility: hidden;}
#    .stAppToolbar {display: none !important;}
#    [data-testid="stToolbar"] {display: none !important;}
#    [data-testid="stSidebar"] {
#       display: block !important;
#       visibility: visible !important;
#    }
#    </style>
# """
# st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==========================================
# AUTHENTICATION SETUP
# ==========================================
# Change these to your preferred secure credentials
VALID_USERNAME = st.secrets["credentials"]["username"]
VALID_PASSWORD = st.secrets["credentials"]["password"]

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def login_screen():
    st.title("🔒 Restricted Access")
    st.markdown("Please log in to access the Dolly Dynamic CG & Risk Evaluation Tool.")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:

            # Strip spaces and normalize inputs
          if username.strip() == VALID_USERNAME.strip() and password.strip() == VALID_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
          else:
            st.error("❌ Invalid Username or Password")

           # if username == VALID_USERNAME and password == VALID_PASSWORD:
          #      st.session_state["authenticated"] = True
            #    st.rerun()
          #  else:
               # st.error("❌ Invalid Username or Password")

# ==========================================
# MAIN APPLICATION
# ==========================================
def main_app():
    # Logout button in the sidebar
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"authenticated": False}))
    st.sidebar.markdown("---")

    st.title("🚜 Dolly Dynamic CG & Risk Evaluation Generator")
    st.markdown("Generates an industrial-standard PDF evaluation dashboard matching dynamic stability requirements.")

    # --- SIDEBAR INPUTS ---
    st.sidebar.header("1. Dolly Identification & Specifications")
    dolly_name = st.sidebar.text_input("Dolly Name / Model", "S-5 DOLLY")
    length = st.sidebar.number_input("Length (L) [mm]", min_value=100.0, value=1200.0, step=10.0)
    width = st.sidebar.number_input("Width (W) [mm]", min_value=100.0, value=600.0, step=10.0)
    height = st.sidebar.number_input("Height (H) [mm]", min_value=100.0, value=1250.0, step=10.0)
    weight = st.sidebar.number_input("Loaded Weight [kg]", min_value=1.0, value=180.0, step=5.0)

    st.sidebar.header("2. Dynamic Acceleration Assumptions")
    acc_push = st.sidebar.number_input("Push Acceleration (g)", min_value=0.05, value=0.30, step=0.05)
    acc_brake = st.sidebar.number_input("Sudden Brake Deceleration (g)", min_value=0.05, value=0.50, step=0.05)
    acc_turn = st.sidebar.number_input("Side Turning Acceleration (g)", min_value=0.05, value=0.20, step=0.05)
    g_val = 9.81  # m/s^2

    st.sidebar.header("3. Dolly Photo Upload")
    uploaded_image = st.sidebar.file_uploader("Upload Dolly Photo (JPG/PNG)", type=["jpg", "jpeg", "png"])

    st.sidebar.header("4. Sign-off Details")
    prepared_by = st.sidebar.text_input("Prepared By", "Production Engineering")
    checked_by = st.sidebar.text_input("Checked By", "Safety Lead")
    approved_by = st.sidebar.text_input("Approved By", "Plant Manager")

    # --- CORE ENGINEERING CALCULATIONS ---
    cg_x_stat = length / 2
    cg_y_stat = width / 2
    cg_z_stat = height * 0.58  # Default loaded CG height (~58% total height)

    delta_x_push = cg_z_stat * acc_push
    delta_x_brake = cg_z_stat * acc_brake
    delta_y_turn = cg_z_stat * acc_turn

    cg_push = (cg_x_stat + delta_x_push, cg_y_stat, cg_z_stat)
    cg_brake = (cg_x_stat + delta_x_brake, cg_y_stat, cg_z_stat)
    cg_turn = (cg_x_stat, cg_y_stat + delta_y_turn, cg_z_stat)

    dsi_push = (length / 2) / cg_push[0] if cg_push[0] > 0 else 0
    dsi_brake = (length / 2) / cg_brake[0] if cg_brake[0] > 0 else 0

    def get_risk_level(dsi):
        if dsi > 1.20: return "SAFE", (0, 150, 0)
        elif 1.00 <= dsi <= 1.20: return "ACCEPTABLE", (0, 100, 250)
        elif 0.80 <= dsi < 1.00: return "MODERATE", (255, 140, 0)
        else: return "HIGH RISK", (200, 0, 0)

    overall_risk_text, overall_risk_color = get_risk_level(dsi_brake)

    # --- DASHBOARD PREVIEW ---
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.subheader("📋 Static & Dynamic Metrics")
        st.write(f"**Static CG:** `{cg_x_stat:.1f}, {cg_y_stat:.1f}, {cg_z_stat:.1f} mm`")
        st.write(f"**Brake Dynamic Shift:** `{delta_x_brake:.1f} mm` -> `{cg_brake[0]:.1f} mm`")
    with col_right:
        st.subheader("⚠️ Dynamic Stability Index (DSI)")
        st.metric("DSI (Sudden Brake Worst-Case)", f"{dsi_brake:.2f}")
        st.markdown(f"**Overall Risk Status:** `{overall_risk_text}`")

    # --- SUPPORT POLYGON DIAGRAM ---
    def generate_support_polygon_diagram():
        fig, ax = plt.subplots(figsize=(4, 2.5), dpi=200)
        rect = plt.Rectangle((0, 0), length, width, facecolor='#E2EFDA', edgecolor='#375623', linewidth=2)
        ax.add_patch(rect)
        w_w, w_h = length * 0.08, width * 0.15
        for px, py in [(0,0), (length-w_w,0), (0,width-w_h), (length-w_w,width-w_h)]:
            ax.add_patch(plt.Rectangle((px, py), w_w, w_h, color='black'))
        ax.plot(cg_x_stat, cg_y_stat, 'yo', markeredgecolor='black', markersize=8, label='Static CG')
        ax.plot(cg_brake[0], cg_brake[1], 'ro', markersize=8, label='Dynamic CG')
        ax.set_xlim(-length*0.1, length*1.1)
        ax.set_ylim(-width*0.2, width*1.2)
        ax.legend(loc='lower right', fontsize=7)
        ax.axis('off')
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        plt.savefig(tmp_path, bbox_inches='tight')
        plt.close()
        return tmp_path

    # --- PDF GENERATOR ---
    class IndustrialReportPDF(FPDF):
        def header(self): pass
        def footer(self): pass

    def generate_pdf():
        pdf = IndustrialReportPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_margins(8, 8, 8)
        pdf.set_auto_page_break(auto=False)

        NAVY = (15, 37, 55)
        LIGHT_BLUE = (222, 235, 247)
        WHITE = (255, 255, 255)

        # 0. TITLE BANNER
        pdf.set_fill_color(*NAVY)
        pdf.rect(8, 8, 194, 10, style='F')
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(10, 9)
        pdf.cell(190, 8, f"{dolly_name.upper()} - DYNAMIC CG CALCULATION & RISK EVALUATION", align='C')

        # 1. TOP ROW: DETAILS, STATIC CG, ASSUMPTIONS, IMAGE, DIMS
        y_top = 20
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_xy(8, y_top)
        pdf.cell(60, 5, "DOLLY DETAILS", border=1, align='C', fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 8)
        details = [("Dolly Name", dolly_name), ("Length (L)", f"{length:.0f} mm"), 
                   ("Width (W)", f"{width:.0f} mm"), ("Height (H)", f"{height:.0f} mm"), 
                   ("Loaded Weight", f"{weight:.0f} kg")]
        cy = y_top + 5
        for lbl, val in details:
            pdf.set_xy(8, cy)
            pdf.cell(30, 4.5, lbl, border=1)
            pdf.cell(30, 4.5, val, border=1, align='C')
            cy += 4.5

        cy += 2
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_xy(8, cy)
        pdf.cell(60, 5, "ESTIMATED STATIC CG", border=1, align='C', fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 8)
        cg_dets = [("CG-X (Length)", f"{cg_x_stat:.0f} mm"), ("CG-Y (Width)", f"{cg_y_stat:.0f} mm"),
                   ("CG-Z (Height)", f"{cg_z_stat:.0f} mm"), ("Reference Point", "Front-Left-Bottom")]
        cy += 5
        for lbl, val in cg_dets:
            pdf.set_xy(8, cy)
            pdf.cell(30, 4.5, lbl, border=1)
            pdf.cell(30, 4.5, val, border=1, align='C')
            cy += 4.5

        cy += 2
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.rect(8, cy, 60, 5, 'F')
        pdf.rect(8, cy, 60, 23, 'D') 
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_xy(8, cy)
        pdf.cell(60, 5, "ASSUMPTIONS", align='C')
        pdf.set_font('Helvetica', '', 7)
        pdf.set_xy(10, cy + 6)
        pdf.multi_cell(56, 3.5, f"- Push accel = {acc_push} g ({acc_push*g_val:.2f} m/s²)\n- Stop/Brake = {acc_brake} g ({acc_brake*g_val:.2f} m/s²)\n- Side turn = {acc_turn} g ({acc_turn*g_val:.2f} m/s²)\n- g (gravity) = {g_val} m/s²")

        pdf.rect(72, y_top, 70, 56)
        if uploaded_image:
            img = Image.open(uploaded_image).convert('RGB')
            tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
            img.save(tmp_img)
            pdf.image(tmp_img, x=73, y=y_top+1, w=68, h=54)
            os.remove(tmp_img)
        else:
            pdf.set_xy(72, y_top+25)
            pdf.cell(70, 5, "[ Image Placeholder ]", align='C')

        pdf.rect(146, y_top, 56, 56)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_xy(146, y_top+2)
        pdf.cell(56, 5, "DIMENSIONS & LIMITS", align='C')
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_xy(148, y_top+10)
        pdf.multi_cell(52, 4, f"Z (Height) = {height:.0f} mm\nY (Width) = {width:.0f} mm\nX (Length) = {length:.0f} mm\n\nSupport Base Limits:\nHalf Wheelbase (L/2) = {length/2:.0f} mm\nHalf Track (W/2) = {width/2:.0f} mm\n\nStatic CG Vector:\n[{cg_x_stat:.0f}, {cg_y_stat:.0f}, {cg_z_stat:.0f}] mm")

        # 2. DYNAMIC CG SHIFT CALCULATION
        y_dyn = 80
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_xy(8, y_dyn)
        pdf.cell(194, 6, "1. DYNAMIC CG SHIFT CALCULATION", border=1, align='C', fill=True)

        col_w = 63.3
        conds = [
            ("1.1 NORMAL PUSH", acc_push, delta_x_push, cg_push, "X (Fwd)"),
            ("1.2 SUDDEN BRAKE", acc_brake, delta_x_brake, cg_brake, "X (Fwd Limit)"),
            ("1.3 SIDE TURNING", acc_turn, delta_y_turn, cg_turn, "Y (Lateral)")
        ]

        y_dyn_box = y_dyn + 7
        for idx, (title, acc, delta, vec, direc) in enumerate(conds):
            cx = 8 + idx * (col_w + 2)
            pdf.set_fill_color(*LIGHT_BLUE)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_xy(cx, y_dyn_box)
            pdf.cell(col_w, 5, title, border=1, align='C', fill=True)
            pdf.rect(cx, y_dyn_box+5, col_w, 24)
            pdf.set_font('Helvetica', '', 7.5)
            pdf.set_xy(cx+2, y_dyn_box+6)
            formula_txt = f"Formula: Delta = (h * a) / g\nh = {cg_z_stat:.0f} mm, a = {acc}g\nDelta = ({cg_z_stat:.0f} * {acc}g) / g = {delta:.1f} mm\n\nResulting Dynamic CG Vector:\n({vec[0]:.0f}, {vec[1]:.0f}, {vec[2]:.0f}) mm"
            pdf.multi_cell(col_w-4, 3.8, formula_txt, align='L')

        # 3. STABILITY CHECK & DSI
        y_stab = 123
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_xy(8, y_stab)
        pdf.cell(118, 6, "2. STABILITY CHECK", border=1, align='C', fill=True)
        pdf.set_xy(128, y_stab)
        pdf.cell(74, 6, "3. DYNAMIC STABILITY INDEX (DSI)", border=1, align='C', fill=True)
        
        # Stability Check Table
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 7)
        cols_stab = ["Condition", "Dyn X", "Dyn Y", "Dyn Z", "L/2 Lim", "W/2 Lim", "Result"]
        w_stab = [22, 14, 14, 14, 18, 18, 18]
        pdf.set_xy(8, y_stab + 7)
        for w, h in zip(w_stab, cols_stab): pdf.cell(w, 5, h, border=1, align='C')
        
        pdf.set_font('Helvetica', '', 7)
        rows_stab = [
            ("Static", cg_x_stat, cg_y_stat, cg_z_stat, length/2, width/2, "STABLE"),
            (f"Push ({acc_push}g)", cg_push[0], cg_push[1], cg_push[2], length/2, width/2, "STABLE"),
            (f"Brake ({acc_brake}g)", cg_brake[0], cg_brake[1], cg_brake[2], length/2, width/2,
        overall_risk_text),
            (f"Turn ({acc_turn}g)", cg_turn[0], cg_turn[1], cg_turn[2], length/2, width/2, "MODERATE")
        ]
        cy = y_stab + 12
        for r in rows_stab:
            pdf.set_xy(8, cy)
            pdf.cell(w_stab[0], 4.5, r[0], border=1)
            pdf.cell(w_stab[1], 4.5, f"{r[1]:.0f}", border=1, align='C')
            pdf.cell(w_stab[2], 4.5, f"{r[2]:.0f}", border=1, align='C')
            pdf.cell(w_stab[3], 4.5, f"{r[3]:.0f}", border=1, align='C')
            pdf.cell(w_stab[4], 4.5, f"{r[4]:.0f}", border=1, align='C')
            pdf.cell(w_stab[5], 4.5, f"{r[5]:.0f}", border=1, align='C')
            pdf.cell(w_stab[6], 4.5, r[6], border=1, align='C')
            cy += 4.5
        # DSI Matrix
        pdf.set_xy(128, y_stab + 7)
        pdf.set_font('Helvetica', 'B', 7)
        pdf.cell(74, 5, f"Formula: DSI = (Half Wheelbase) / Dynamic CG_X", border=1, align='C')
        pdf.set_xy(128, y_stab + 12)
        for w, h in zip([28, 15, 12, 19], ["Condition", "Dyn CG-X", "DSI", "Risk Level"]):
          pdf.cell(w, 5, h, border=1, align='C')
            
        pdf.set_font('Helvetica', '', 7)
        dsi_rows = [("Normal Push", cg_push[0], dsi_push, get_risk_level(dsi_push)[0]),
            ("Sudden Brake", cg_brake[0], dsi_brake, overall_risk_text)]
        cy_dsi = y_stab + 17
        for r in dsi_rows:
            pdf.set_xy(128, cy_dsi)
            pdf.cell(28, 4.5, r[0], border=1)
            pdf.cell(15, 4.5, f"{r[1]:.0f}", border=1, align='C')
            pdf.cell(12, 4.5, f"{r[2]:.2f}", border=1, align='C')
            pdf.cell(19, 4.5, r[3], border=1, align='C')
            cy_dsi += 4.5
        # Scale legend cleanly positioned above the next section
        pdf.set_xy(128, cy_dsi + 1)
        pdf.set_font('Helvetica', 'B', 5.5)
        pdf.cell(74, 3.5, (
           "SCALE: >1.20 (SAFE) | 1.0-1.20 (ACCEPT) | "
           "0.8-1.0 (MODERATE) | <0.8 (HIGH RISK)"
        ), align='C')

        # 4. RESULT SUMMARY & 5. RECOMMENDATIONS & 6. DIAGRAM (Shifted y_res down to 162)
        y_res = 162
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_xy(8, y_res)
        pdf.cell(60, 6, "4. RESULT SUMMARY", border=1, align='C', fill=True)
        pdf.set_xy(72, y_res)
        pdf.cell(64, 6, "5. RECOMMENDATIONS", border=1, align='C', fill=True)
        pdf.set_xy(140, y_res)
        pdf.cell(62, 6, "6. SUPPORT POLYGON", border=1, align='C', fill=True)
        pdf.set_text_color(0, 0, 0)
        # Summary Box Frame
        pdf.rect(8, y_res+6, 60, 25)
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_xy(10, y_res+7.5)
        sum_txt = (f"Static CG: ({cg_x_stat:.0f}, {cg_y_stat:.0f}, {cg_z_stat:.0f}) mm\n"
                   f"Push CG: ({cg_push[0]:.0f}, {cg_push[1]:.0f}, {cg_push[2]:.0f}) mm\n"
                   f"Brake CG: ({cg_brake[0]:.0f}, {cg_brake[1]:.0f}, {cg_brake[2]:.0f}) mm\n"
                   f"Turn CG: ({cg_turn[0]:.0f}, {cg_turn[1]:.0f}, {cg_turn[2]:.0f}) mm"
                  )
        pdf.multi_cell(56, 3.5, sum_txt)
        
        # --- COLOR-CODED OVERALL EVALUATION BADGE ---
        
        pdf.set_xy(10, y_res + 23)
        pdf.set_font('Helvetica', 'B', 7.5)
        pdf.cell(22, 5, "OVERALL EVAL:", align='L')
        
        # Determine colors: GREEN, YELLOW, ORANGE, RED
        if "SAFE" in overall_risk_text:
           bg_color, fg_color = (0, 150, 0), (255, 255, 255) # GREEN (White text)
        elif "ACCEPT" in overall_risk_text:
           bg_color, fg_color = (255, 220, 0), (0, 0, 0) # YELLOW (Black text)
        elif "MODERATE" in overall_risk_text:
           bg_color, fg_color = (255, 140, 0), (255, 255, 255) # ORANGE (White text)
        else:
           bg_color, fg_color = (200, 0, 0), (255, 255, 255) # RED / HIGH RISK (White text)

        # Draw color background rectangle and label text
        pdf.set_fill_color(*bg_color)
        pdf.rect(33, y_res + 23.5, 33, 5, 'F')
        pdf.set_xy(33, y_res + 23.5)
        pdf.set_font('Helvetica', 'B', 7.5)
        pdf.set_text_color(*fg_color)
        pdf.cell(33, 5, overall_risk_text, align='C')
        pdf.set_text_color(0, 0, 0) # Reset font color back to black

        # Recommendations Box
        pdf.rect(72, y_res+6, 64, 25)
        pdf.set_xy(74, y_res+8)
        rec_txt = (
           "- Limit dolly speed to <= 3 km/h.\n"
           "- Avoid sudden stops and sharp turns.\n"
           "- Reduce CG height whenever possible.\n"
           "- Ensure load is properly secured.\n"
           "- Use dolly on smooth, level floors only."
        )
        pdf.multi_cell(60, 3.8, rec_txt)

        # Polygon Box
        pdf.rect(140, y_res+6, 62, 25)
        poly_img = generate_support_polygon_diagram()
        pdf.image(poly_img, x=142, y=y_res+7, w=58, h=23)
        os.remove(poly_img)

        # 7. RISK EVALUATION HAZARD MATRIX
        y_haz = 191
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_xy(8, y_haz)
        pdf.cell(194, 6, "7. RISK EVALUATION HAZARD MATRIX", border=1, align='C', fill=True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 7)
        cols_haz = ["HAZARD", "POSSIBLE EFFECT", "SEVERITY (1-5)", "LIKELIHOOD (1-5)", "RATING (SxL)", "RISK LEVEL"]
        w_haz = [54, 50, 25, 25, 20, 20]
        pdf.set_xy(8, y_haz + 7)
        for w, h in zip(w_haz, cols_haz): pdf.cell(w, 5, h, border=1, align='C')

        pdf.set_font('Helvetica', '', 7)
        haz_rows = [
            ("1. Toppling due to sudden dynamic braking", "Injury, Damage to parts", "4", "3", "12", "HIGH RISK" if "HIGH" in overall_risk_text else "MEDIUM"),
            ("2. Instability on uneven floor conditions", "Caster damage, Load shift", "3", "2", "6", "LOW"),
            ("3. Overloading structure", "Frame/Caster failure", "5", "1", "5", "LOW")
        ]
        cy = y_haz + 12
        for r in haz_rows:
            pdf.set_xy(8, cy)
            pdf.cell(w_haz[0], 5, r[0], border=1)
            pdf.cell(w_haz[1], 5, r[1], border=1)
            pdf.cell(w_haz[2], 5, r[2], border=1, align='C')
            pdf.cell(w_haz[3], 5, r[3], border=1, align='C')
            pdf.cell(w_haz[4], 5, r[4], border=1, align='C')
            pdf.cell(w_haz[5], 5, r[5], border=1, align='C')
            cy += 5

        # 8. SIGN OFF (BOTTOM)
        # y_sign = 275
        # pdf.set_text_color(0, 0, 0)
        # pdf.set_font('Helvetica', '', 8)
        # blocks = [("PREPARED BY", prepared_by, datetime.date.today().strftime("%d-%m-%Y")),
        #           ("CHECKED BY", checked_by, "---"),
        #           ("APPROVED BY", approved_by, "---")]
        # for idx, (role, name, dt) in enumerate(blocks):
        #     bx = 8 + idx * 65
        #     pdf.set_xy(bx, y_sign)
        #     pdf.cell(60, 4, f"{role}: {name}", border='LTR')
        #     pdf.set_xy(bx, y_sign + 4)
        #     pdf.cell(60, 4, f"DATE: {dt}", border='LBR')

        return bytes(pdf.output())


    # --- DOWNLOAD BUTTON ---
    st.markdown("---")
    if st.button("📄 Generate & Download Dashboard PDF Report", type="primary"):
        pdf_data = generate_pdf()
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_data,
            file_name=f"{dolly_name.replace(' ', '_')}_CG_Evaluation.pdf",
            mime="application/pdf"
        )

# ==========================================
# GATEKEEPER ROUTING
# ==========================================
if not st.session_state["authenticated"]:
    login_screen()
else:
    main_app()
