"""

@Author:    Danish Ansari - Osdag Team, IIT Bombay
@Co-author: Aditya Pawar, Project Intern, MIT College (Aurangabad)


@Module - Base Plate Connection
           - Pinned Base Plate (welded and bolted) [Axial + Shear]
           - Gusseted Base Plate [Moment (major and minor axis) + Axial + Shear]
           - Base Plate for hollow sections [Moment (major and minor axis) + Axial + Shear]


@Reference(s): 1) IS 800: 2007, General construction in steel - Code of practice (Third revision)
               2) IS 808: 1989, Dimensions for hot rolled steel beam, column, channel, and angle sections and
                                it's subsequent revision(s)
               3) IS 2062: 2011, Hot rolled medium and high tensile structural steel - specification
               4) IS 5624: 1993, Foundation bolts
               5) IS 456: 2000, Plain and reinforced concrete - code of practice
               6) Design of Steel Structures by N. Subramanian (Fifth impression, 2019, Chapter 15)
               7) Limit State Design of Steel Structures by S K Duggal (second edition, Chapter 11)

     other     8)  Column Bases - Omer Blodgett (chapter 3)
  references   9) AISC Design Guide 1 - Base Plate and Anchor Rod Design

"""

# Importing modules from the project directory

from design_type.connection.moment_connection import MomentConnection
from utils.common.is800_2007 import IS800_2007
from utils.common.other_standards import IS_5624_1993
from utils.common.component import *
from utils.common.material import *
from utils.common.common_calculation import *
from Common import *
from utils.common.load import Load
from utils.common.other_standards import *
from design_report.reportGenerator import save_html
from cad.common_logic import CommonDesignLogic

import logging


class BasePlateConnection(MomentConnection, IS800_2007, IS_5624_1993, IS1367_Part3_2002, Column, CommonDesignLogic):
    """
    Perform stress analyses --> design base plate and anchor bolt--> provide connection detailing.

    Attributes:
                connectivity (str): type of base plate connection (pinned - welded, pinned - bolted,
                                    gusseted, hollow section).
                end_condition (str): assume end condition based on base plate type.
                    Assumption(s):
                                1) End condition is 'Pinned' for welded and bolted base plate.
                                2) End condition is 'Fixed' for gusseted and hollow section type base plate.

                column_section (str): column section [Ref: IS 808: 1989, and it's subsequent revision(s),
                                any new section data added by the user using the 'add section' feature from Osdag GUI.
                material (str): material grade of the column section [Ref: IS 2062: 2011, table 2].

                load_axial (float): Axial compressive load (concentric to column axis).
                load_shear (float): Shear/horizontal load.
                load_moment_major (float): Bending moment acting along the major (z-z) axis of the column.
                load_moment_minor (float): Bending moment acting along the minor (y-y) axis of the column.

                anchor_dia (str): diameter of the anchor bolt [Ref: IS 5624: 1993, page 5].
                anchor_type (str): type of the anchor bolt [Ref: IS 5624: 1993, Annex A, clause 4].

                footing_grade (str): grade of footing material (concrete) [Ref: IS 456: 2000, table 2].

                dp_column_designation (str): designation of the column as per IS 808.
                dp_column_type (str): type of manufacturing of the coulmn section (rolled, built-up, welded etc.).
                dp_column_source (str): source of the database of the column section.
                                        [Osdag/ResourceFiles/Database/Intg_osdag.sqite].
                dp_column_material (str): material grade of the column section [Ref: IS 2062: 2011].
                dp_column_fu (float): ultimate strength of the column section (default if not overwritten).
                dp_column_fy (float): yield strength of the column section (default if not overwritten).

                dp_bp_material (str): material grade of the base plate [Ref: IS 2062: 2011].
                dp_bp_fu (float): ultimate strength of the base plate (default if not overwritten).
                dp_bp_fy (float): yield strength of the base plate (default if not overwritten).
                    Assumption: The ultimate and yield strength values of base plare are assumed to be same as the
                                parent (column) material unless and untill overwritten in the design preferences,
                                with suitable validation.

                dp_anchor_designation (str): designation of the anchor bolt as per IS 5624: 1993, clause 5.
                dp_anchor_type (str): type of the anchor bolt [Ref: IS 5624: 1993, Annex A, clause 4].
                dp_anchor_hole (str): type of hole 'Standard' or 'Over-sized'.
                dp_anchor_fu_overwrite (float): ultimate strength of the anchor bolt corresponding to its grade.
                dp_anchor_friction (float): coefficient of friction between the anchor bolt and the footing material.

                dp_weld_fab (str): type of weld fabrication, 'Shop Weld' or 'Field Weld'.
                dp_weld_fu_overwrite (float): ultimate strength of the weld material.

                dp_detail_edge_type (str): type of edge preparation, 'a - hand flame cut' or 'b - Machine flame cut'.
                dp_detail_is_corrosive (str): is environment corrosive, 'Yes' or 'No'.

                dp_design_method (str): design philosophy used 'Limit State Design'.
                dp_bp_method (str): analysis method used for base plate 'Effective Area Method'

                gamma_m0 (float): partial safety factor for material - resistance governed by yielding or buckling.
                gamma_m1 (float): partial safety factor for material - resistance governed by ultimate stress.
                gamma_mb (float): partial safety factor for material - resistance of connection - bolts.
                gamma_mw (float): partial safety factor for material - resistance of connection - weld.

                bearing_strength_concrete (float)

    """

    def __init__(self):
        """Initialize all attributes."""
        super(BasePlateConnection, self).__init__()

        # attributes for input dock UI
        self.connectivity = ""
        self.end_condition = ""
        self.column_section = ""
        self.material = ""

        self.load_axial_compression = 0.0
        self.load_axial_tension = 0.0
        # self.load_shear = 0.0
        self.load_shear_major = 0.0
        self.load_shear_minor = 0.0
        self.load_moment_major = 0.0
        self.load_moment_minor = 0.0

        self.shear_resistance = 0.0
        self.shear_key_required = 'No'
        self.shear_key_thk = self.plate_thk

        self.shear_key_along_ColDepth = 'No'
        self.shear_key_len_ColDepth = self.column_D
        self.shear_key_depth_ColDepth = 0.0

        self.shear_key_along_ColWidth = 'No'
        self.shear_key_len_ColWidth = self.column_bf
        self.shear_key_depth_ColWidth = 0.0

        self.anchor_dia = []
        self.anchor_type = ""
        self.anchor_grade = []
        self.anchor_fu_fy = []

        self.footing_grade = 0.0

        if self.connectivity == 'Welded Column Base':
            self.weld_type = self.weld_type
        else:
            self.weld_type = 'Butt Weld'

        # attributes for design preferences
        self.dp_column_designation = ""  # dp for column
        self.dp_column_type = ""
        self.dp_column_source = ""
        self.dp_column_material = ""
        self.dp_column_fu = 0.0
        self.dp_column_fy = 0.0

        self.dp_bp_material = ""  # dp for base plate
        self.dp_bp_fu = 0.0
        self.dp_bp_fy = 0.0

        self.dp_anchor_designation = ""  # dp for anchor bolt
        self.dp_anchor_type = ""
        self.dp_anchor_hole = "Standard"
        self.dp_anchor_length = 0
        self.dp_anchor_fu_overwrite = 0.0
        self.dp_anchor_friction = 0.0

        self.dp_weld_fab = "Shop Weld"  # dp for weld
        self.dp_weld_fu_overwrite = 0.0

        self.dp_detail_edge_type = "b - Machine flame cut"  # dp for detailing
        self.dp_detail_is_corrosive = "No"

        self.dp_design_method = "Limit State Design"  # dp for design
        self.dp_bp_method = "Effective Area Method"

        # other attributes
        self.gamma_m0 = 0.0
        self.gamma_m1 = 0.0
        self.gamma_mb = 0.0
        self.gamma_mw = 0.0

        # self.column_properties = Column(designation=self.dp_column_designation, material_grade=self.dp_column_material)
        self.column_D = 0.0
        self.column_bf = 0.0
        self.column_tf = 0.0
        self.column_tw = 0.0
        self.column_r1 = 0.0
        self.column_r2 = 0.0

        self.bearing_strength_concrete = 0.0
        self.w = 0.0
        self.min_area_req = 0.0
        self.effective_bearing_area = 0.0
        self.projection = 0.0
        self.plate_thk = 0.0
        self.standard_plate_thk = []
        self.neglect_anchor_dia = []
        self.anchor_bolt = ''
        self.anchor_dia_provided = 20
        self.grout_thk = 50
        self.plate_washer_thk = 1
        self.nut_thk = 1
        self.anchor_length_min = 1
        self.anchor_length_max = 1
        self.anchor_length_provided = 1
        self.anchor_len_below_footing = 1
        self.anchor_len_above_footing = 1
        self.anchor_nos_provided = 0
        self.anchor_hole_dia = 0.0
        self.bp_length_min = 0.0
        self.bp_width_min = 0.0
        self.bp_length_provided = 0.0
        self.bp_width_provided = 0.0
        self.end_distance = 0.0
        self.end_distance_max = 0.0
        self.edge_distance = 0.0
        self.edge_distance_max = 0.0
        self.pitch_distance = 0.0
        self.gauge_distance = 0.0
        self.bp_area_provided = 0.0
        self.anchor_area = self.bolt_area(self.table1(self.anchor_dia_provided)[0])  # TODO check if this works
        self.shear_capacity_anchor = 0.0
        self.bearing_capacity_anchor = 0.0
        self.anchor_capacity = 0.0
        self.v_sb = 0.0
        self.v_db = 0.0
        self.t_b = 0.0
        self.t_db = 0.0
        self.combined_capacity_anchor = 0.0

        self.moment_bp_case = ''

        self.length_available_total = 0.0
        self.effective_length_flange = 0.0
        self.total_eff_len_available = 0.0
        self.effective_length_web = 0.0
        self.load_axial_flange = 0.0
        self.load_axial_web = 0.0
        self.strength_unit_len = 0.0
        self.weld_size = 0.0
        self.weld_fu = 0.0
        self.weld_size_flange_max = 0.0
        self.weld_size_web_max = 0.0

        self.weld_size_flange = 0.0
        self.weld_size_web = 0.0
        self.gusset_along_flange = 'No'
        self.gusset_along_web = 'No'
        self.gusset_plate_length = 0.0
        self.stiffener_plate_length = 0.0
        self.total_eff_len_gusset_available = 0.0
        self.gusset_outstand_length = 0.0
        self.stiffener_outstand_length = 0.0
        self.gusset_fy = self.dp_column_fy
        self.stiffener_fy = self.dp_column_fy
        self.epsilon = 1
        self.gusset_plate_thick = 0.0
        self.stiffener_plate_thick = 0.0
        self.gusset_plate_height = 0.0
        self.stiffener_plate_height = 0.0
        self.stiffener_plt_len_along_flange = 0.0
        self.stiffener_plt_len_along_web = 0.0
        self.stiffener_plt_len_across_web = 0.0

        self.stiffener_plt_thick_along_flange = 0.0
        self.stiffener_plt_thick_along_web = 0.0
        self.stiffener_plt_thick_across_web = 0.0
        self.stiffener_plt_height_along_flange = 0.0
        self.stiffener_plt_height_along_web = 0.0
        self.stiffener_plt_height_across_web = 0.0

        self.stiffener_along_flange = ''
        self.stiffener_along_web = ''
        self.stiffener_across_web = ''
        self.eff_stiffener_plt_len_along_flange = 0.0
        self.eff_stiffener_plt_len_along_web = 0.0

        self.stiffener_plt_thick_btwn_D = 0.0
        self.stiffener_plt_len_btwn_D = 0.0
        self.stiffener_plt_height_btwn_D = 0.0

        self.shear_on_gusset = 0.0
        self.moment_on_gusset = 0.0
        self.shear_capacity_gusset = 0.0
        self.z_e_gusset = 0.0
        self.moment_capacity_gusset = 0.0

        self.shear_on_stiffener_along_flange = 0.0
        self.shear_capa_stiffener_along_flange = 0.0
        self.moment_on_stiffener_along_flange = 0.0
        self.moment_capa_stiffener_along_flange = 0.0
        self.z_e_stiffener_along_flange = 0.0

        self.shear_on_stiffener_along_web = 0.0
        self.shear_capa_stiffener_along_web = 0.0
        self.moment_on_stiffener_along_web = 0.0
        self.moment_capa_stiffener_along_web = 0.0
        self.z_e_stiffener_along_web = 0.0

        self.shear_on_stiffener_across_web = 0.0
        self.shear_capa_stiffener_across_web = 0.0
        self.moment_on_stiffener_across_web = 0.0
        self.moment_capa_stiffener_across_web = 0.0
        self.z_e_stiffener_across_web = 0.0

        self.weld_size_gusset = 0.0
        self.weld_size_stiffener = 0.0
        self.weld_size_vertical_flange = 0.0
        self.weld_size_vertical_web = 0.0

        self.eccentricity_zz = 0.0
        self.sigma_max_zz = 0.0
        self.sigma_min_zz = 0.0
        self.critical_xx = 0.0
        self.sigma_xx = 0.0
        self.sigma_web = 0.0
        self.ze_zz = 0.0
        self.critical_M_xx = 0.0
        self.n = 1
        self.anchor_area_tension = 0.0
        self.f = 0.0
        self.y = 0.0
        self.tension_demand_anchor = 0.0
        self.tension_capacity_anchor = 0.0
        self.tension_capacity_anchor_uplift = self.tension_capacity_anchor
        self.tension_bolts_req = 1

        self.anchor_inside_flange = 'No'
        self.anchor_dia_uplift = self.anchor_dia_provided
        self.anchor_grade_tension = self.anchor_grade
        self.anchor_tension_capa = 0.0
        self.anchor_nos_tension = 0.0
        self.anchor_nos_uplift = 0.0

        self.safe = True

    def set_osdaglogger(key):
        """
        Set logger for Base Plate Module.
        """
        global logger
        logger = logging.getLogger('osdag')

        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        handler = logging.FileHandler('logging_text.log')

        formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if key is not None:
            handler = OurLog(key)
            formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    def module_name(self):
        """
        Call the Base Plate Module key for displaying the module name.
        """
        return KEY_DISP_BASE_PLATE

    def input_values(self, existingvalues={}):
        """
        Return a-list of tuple, used to create the Base Plate input dock U.I in Osdag design window.
        """

        self.module = KEY_DISP_BASE_PLATE

        options_list = []

        if KEY_DISP_CONN in existingvalues:
            existingvalue_key_conn = existingvalues[KEY_DISP_CONN]
        else:
            existingvalue_key_conn = ''

        if KEY_SUPTNGSEC in existingvalues:  # this might not be required
            existingvalue_key_suptngsec = existingvalues[KEY_SUPTNGSEC]
        else:
            existingvalue_key_suptngsec = ''

        if KEY_SUPTDSEC in existingvalues:
            existingvalue_key_suptdsec = existingvalues[KEY_SUPTDSEC]
        else:
            existingvalue_key_suptdsec = ''

        if KEY_MATERIAL in existingvalues:
            existingvalue_key_mtrl = existingvalues[KEY_MATERIAL]
        else:
            existingvalue_key_mtrl = ''

        if KEY_AXIAL in existingvalues:
            existingvalue_key_axial = existingvalues[KEY_AXIAL]
        else:
            existingvalue_key_axial = ''

        if KEY_MOMENT in existingvalues:
            existingvalue_key_versh = existingvalues[KEY_MOMENT]
        else:
            existingvalue_key_versh = ''

        if KEY_SHEAR in existingvalues:
            existingvalue_key_versh = existingvalues[KEY_SHEAR]
        else:
            existingvalue_key_versh = ''

        if KEY_DIA_ANCHOR in existingvalues:
            existingvalue_key_d = existingvalues[KEY_DIA_ANCHOR]
        else:
            existingvalue_key_d = ''

        # if KEY_TYP in existingvalues:
        #     existingvalue_key_typ = existingvalues[KEY_TYP]
        # else:
        #     existingvalue_key_typ = ''

        # if KEY_GRD in existingvalues:
        #     existingvalue_key_grd = existingvalues[KEY_GRD]
        # else:
        #     existingvalue_key_grd = ''

        t1 = (None, DISP_TITLE_CM, TYPE_TITLE, None, None)
        options_list.append(t1)

        t2 = (KEY_MODULE, KEY_DISP_BASE_PLATE, TYPE_MODULE, None, None)
        options_list.append(t2)

        t3 = (KEY_CONN, KEY_DISP_CONN, TYPE_COMBOBOX, existingvalue_key_conn, VALUES_CONN_BP)
        options_list.append(t3)

        t4 = (KEY_IMAGE, None, TYPE_IMAGE, None, "./ResourceFiles/images/base_plate.png")
        options_list.append(t4)

        t5 = (KEY_END_CONDITION, KEY_DISP_END_CONDITION, TYPE_NOTE, existingvalue_key_conn, 'Pinned')
        options_list.append(t5)

        t6 = (KEY_SUPTNGSEC, KEY_DISP_COLSEC, TYPE_COMBOBOX, existingvalue_key_suptngsec,
              connectdb("Columns"))  # this might not be required
        options_list.append(t6)

        # t4 = (KEY_SUPTDSEC, KEY_DISP_BEAMSEC, TYPE_COMBOBOX, existingvalue_key_suptdsec, connectdb("Columns"))
        # options_list.append(t4)

        t7 = (KEY_MATERIAL, KEY_DISP_MATERIAL, TYPE_COMBOBOX, existingvalue_key_mtrl, VALUES_MATERIAL)
        options_list.append(t7)

        t8 = (None, DISP_TITLE_FSL, TYPE_TITLE, None, None)
        options_list.append(t8)

        t9 = (KEY_AXIAL_BP, KEY_DISP_AXIAL_BP, TYPE_TEXTBOX, existingvalue_key_axial, None)
        options_list.append(t9)

        t22 = (KEY_AXIAL_TENSION_BP, KEY_DISP_AXIAL_TENSION_BP, TYPE_TEXTBOX, existingvalue_key_axial, None)
        options_list.append(t22)

        t10 = (KEY_SHEAR_BP, KEY_DISP_SHEAR_BP, '', existingvalue_key_versh, None)
        options_list.append(t10)

        t10 = (KEY_SHEAR_MAJOR, KEY_DISP_SHEAR_MAJOR, TYPE_TEXTBOX, existingvalue_key_versh, None)
        options_list.append(t10)

        t10 = (KEY_SHEAR_MINOR, KEY_DISP_SHEAR_MINOR, TYPE_TEXTBOX, existingvalue_key_versh, None)
        options_list.append(t10)

        t11 = (KEY_MOMENT, KEY_DISP_MOMENT, '', existingvalue_key_axial, None)
        options_list.append(t11)

        t12 = (KEY_MOMENT_MAJOR, KEY_DISP_MOMENT_MAJOR, TYPE_TEXTBOX, existingvalue_key_conn, None)
        options_list.append(t12)

        t13 = (KEY_MOMENT_MINOR, KEY_DISP_MOMENT_MINOR, TYPE_TEXTBOX, existingvalue_key_conn, None)
        options_list.append(t13)

        t14 = (None, DISP_TITLE_ANCHOR_BOLT, TYPE_TITLE, None, None)
        options_list.append(t14)

        t15 = (KEY_DIA_ANCHOR, KEY_DISP_DIA_ANCHOR, TYPE_COMBOBOX_CUSTOMIZED, existingvalue_key_d, VALUES_DIA_ANCHOR)
        options_list.append(t15)

        t16 = (KEY_TYP_ANCHOR, KEY_DISP_TYP_ANCHOR, TYPE_COMBOBOX, existingvalue_key_d, VALUES_TYP_ANCHOR)
        options_list.append(t16)

        t17 = (KEY_GRD_ANCHOR, KEY_DISP_GRD_ANCHOR, TYPE_COMBOBOX_CUSTOMIZED, existingvalue_key_d, VALUES_GRD_ANCHOR)
        options_list.append(t17)

        t18 = (None, DISP_TITLE_FOOTING, TYPE_TITLE, None, None)
        options_list.append(t18)

        t19 = (KEY_GRD_FOOTING, KEY_DISP_GRD_FOOTING, TYPE_COMBOBOX, existingvalue_key_d, VALUES_GRD_FOOTING)
        options_list.append(t19)

        t20 = (None, DISP_TITLE_WELD, TYPE_TITLE, None)
        options_list.append(t20)

        t21 = (KEY_WELD_TYPE, KEY_DISP_WELD_TYPE, TYPE_COMBOBOX, existingvalue_key_d, VALUES_WELD_TYPE)
        options_list.append(t21)

        # t11 = (KEY_TYP, KEY_DISP_TYP, TYPE_COMBOBOX, existingvalue_key_typ, VALUES_TYP)
        # options_list.append(t11)

        # t12 = (KEY_GRD, KEY_DISP_GRD, TYPE_COMBOBOX_CUSTOMIZED, existingvalue_key_grd, VALUES_GRD)
        # options_list.append(t12)

        # t13 = (None, DISP_TITLE_PLATE, TYPE_TITLE, None, None)
        # options_list.append(t13)

        # t14 = (KEY_PLATETHK, KEY_DISP_PLATETHK, TYPE_COMBOBOX_CUSTOMIZED, existingvalue_key_platethk, VALUES_PLATETHK)
        # options_list.append(t14)

        return options_list

    def output_values(self, flag):
        out_list = []

        t1 = (None, DISP_TITLE_ANCHOR_BOLT, TYPE_TITLE, None)
        out_list.append(t1)

        t2 = (KEY_OUT_DIA_ANCHOR, KEY_DISP_OUT_DIA_ANCHOR, TYPE_TEXTBOX, self.anchor_dia_provided if flag else '')
        out_list.append(t2)

        t3 = (KEY_OUT_GRD_ANCHOR, KEY_DISP_OUT_GRD_ANCHOR, TYPE_TEXTBOX, self.anchor_grade if flag else '')
        out_list.append(t3)

        t4 = (KEY_OUT_ANCHOR_BOLT_LENGTH, KEY_DISP_OUT_ANCHOR_BOLT_LENGTH, TYPE_TEXTBOX,
              self.anchor_length_provided if flag else '')
        out_list.append(t4)

        t5 = (KEY_OUT_ANCHOR_BOLT_SHEAR, KEY_OUT_DISP_ANCHOR_BOLT_SHEAR, TYPE_TEXTBOX,
              self.shear_capacity_anchor if flag else '')
        out_list.append(t5)

        t6 = (KEY_OUT_ANCHOR_BOLT_BEARING, KEY_OUT_DISP_ANCHOR_BOLT_BEARING, TYPE_TEXTBOX,
              self.bearing_capacity_anchor if flag else '')
        out_list.append(t6)

        t7 = (KEY_OUT_ANCHOR_BOLT_CAPACITY, KEY_OUT_DISP_ANCHOR_BOLT_CAPACITY, TYPE_TEXTBOX,
              self.anchor_capacity if flag else '')
        out_list.append(t7)

        t8 = (KEY_OUT_ANCHOR_BOLT_COMBINED, KEY_OUT_DISP_ANCHOR_BOLT_COMBINED, TYPE_TEXTBOX,
              self.combined_capacity_anchor if flag else '')
        out_list.append(t8)

        t20 = (KEY_OUT_ANCHOR_BOLT_TENSION, KEY_OUT_DISP_ANCHOR_BOLT_TENSION, TYPE_TEXTBOX,
               self.tension_capacity_anchor if flag and self.connectivity == 'Moment Base Plate' else '')
        out_list.append(t20)

        t101 = (None, DISP_TITLE_ANCHOR_BOLT_UPLIFT, TYPE_TITLE, None)
        out_list.append(t101)

        t101 = (KEY_OUT_DIA_ANCHOR_UPLIFT, KEY_DISP_OUT_DIA_ANCHOR_UPLIFT, TYPE_TEXTBOX,
                self.anchor_dia_uplift if flag and self.connectivity ==
                'Moment Base Plate' and self.load_axial_tension > 0 else '')
        out_list.append(t101)

        t101 = (KEY_OUT_GRD_ANCHOR_UPLIFT, KEY_DISP_OUT_GRD_ANCHOR_UPLIFT, TYPE_TEXTBOX,
                self.anchor_grade_tension if flag and self.connectivity ==
                'Moment Base Plate' and self.load_axial_tension > 0 else '')
        out_list.append(t101)

        t101 = (KEY_OUT_ANCHOR_BOLT_LENGTH_UPLIFT, KEY_DISP_OUT_ANCHOR_BOLT_LENGTH_UPLIFT, TYPE_TEXTBOX,
                self.anchor_length_provided if flag and self.connectivity ==
                'Moment Base Plate' and self.load_axial_tension > 0 else '')
        out_list.append(t101)

        t101 = (KEY_OUT_ANCHOR_BOLT_TENSION_UPLIFT, KEY_OUT_DISP_ANCHOR_BOLT_TENSION_UPLIFT, TYPE_TEXTBOX,
                self.tension_capacity_anchor_uplift if flag and self.connectivity ==
                'Moment Base Plate' and self.load_axial_tension > 0 else '')
        out_list.append(t101)

        t9 = (None, KEY_DISP_BASE_PLATE, TYPE_TITLE, None)
        out_list.append(t9)

        t10 = (KEY_OUT_BASEPLATE_THICKNNESS, KEY_OUT_DISP_BASEPLATE_THICKNNESS, TYPE_TEXTBOX,
               self.plate_thk if flag else '')
        out_list.append(t10)

        t11 = (KEY_OUT_BASEPLATE_LENGTH, KEY_OUT_DISP_BASEPLATE_LENGTH, TYPE_TEXTBOX,
               self.bp_length_provided if flag else '')
        out_list.append(t11)

        t12 = (KEY_OUT_BASEPLATE_WIDTH, KEY_OUT_DISP_BASEPLATE_WIDTH, TYPE_TEXTBOX,
               self.bp_width_provided if flag else '')
        out_list.append(t12)

        t13 = (None, DISP_TITLE_DETAILING, TYPE_TITLE, None)
        out_list.append(t13)

        t14 = (KEY_OUT_DETAILING_NO_OF_ANCHOR_BOLT, KEY_OUT_DISP_DETAILING_NO_OF_ANCHOR_BOLT, TYPE_TEXTBOX,
               self.anchor_nos_provided if flag else '')
        out_list.append(t14)

        t21 = (KEY_OUT_DETAILING_PITCH_DISTANCE, KEY_OUT_DISP_DETAILING_PITCH_DISTANCE, TYPE_TEXTBOX,
               self.pitch_distance if flag else '')
        out_list.append(t21)

        t22 = (KEY_OUT_DETAILING_GAUGE_DISTANCE, KEY_OUT_DISP_DETAILING_GAUGE_DISTANCE, TYPE_TEXTBOX,
               self.gauge_distance if flag else '')
        out_list.append(t22)

        t15 = (KEY_OUT_DETAILING_END_DISTANCE, KEY_OUT_DISP_DETAILING_END_DISTANCE, TYPE_TEXTBOX,
               self.end_distance if flag else '')
        out_list.append(t15)

        t16 = (KEY_OUT_DETAILING_EDGE_DISTANCE, KEY_OUT_DISP_DETAILING_EDGE_DISTANCE, TYPE_TEXTBOX,
               self.edge_distance if flag else '')
        out_list.append(t16)

        t17 = (KEY_OUT_DETAILING_PROJECTION, KEY_OUT_DISP_DETAILING_PROJECTION, TYPE_TEXTBOX,
               self.projection if flag and self.connectivity == 'Welded Column Base' else '')
        out_list.append(t17)

        t23 = (None, DISP_TITLE_STIFFENER_PLATE_FLANGE, TYPE_TITLE, None)
        out_list.append(t23)

        t24 = (KEY_OUT_STIFFENER_PLATE_FLANGE, KEY_DISP_OUT_STIFFENER_PLATE_FLANGE, TYPE_OUT_BUTTON,
               ['Stiffener Details', self.stiffener_flange_details])
        out_list.append(t24)

        # t24 = (KEY_OUT_STIFFENER_PLATE_FLANGE_THICKNNESS, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_THICKNESS, TYPE_TEXTBOX,
        #        self.stiffener_plt_thick_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t24)
        #
        # t25 = (KEY_OUT_STIFFENER_PLATE_FLANGE_SHEAR_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_SHEAR_DEMAND,
        #        TYPE_TEXTBOX, self.shear_on_stiffener_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t25)
        #
        # t26 = (KEY_OUT_STIFFENER_PLATE_FLANGE_SHEAR, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_SHEAR, TYPE_TEXTBOX,
        #        self.shear_capa_stiffener_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t26)
        #
        # t27 = (KEY_OUT_STIFFENER_PLATE_FLANGE_MOMENT_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_MOMENT_DEMAND,
        #        TYPE_TEXTBOX, self.moment_on_stiffener_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t27)
        #
        # t28 = (KEY_OUT_STIFFENER_PLATE_FLANGE_MOMENT, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_MOMENT, TYPE_TEXTBOX,
        #        self.moment_capa_stiffener_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t28)

        # t23 = (None, DISP_TITLE_GUSSET_PLATE, TYPE_TITLE, None)
        # out_list.append(t23)

        # t24 = (KEY_OUT_GUSSET_PLATE_THICKNNESS, KEY_OUT_DISP_GUSSET_PLATE_THICKNESS, TYPE_TEXTBOX,
        #        self.gusset_plate_thick if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t24)
        #
        # t25 = (KEY_OUT_GUSSET_PLATE_SHEAR_DEMAND, KEY_OUT_DISP_GUSSET_PLATE_SHEAR_DEMAND, TYPE_TEXTBOX,
        #        self.shear_on_gusset if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t25)
        #
        # t26 = (KEY_OUT_GUSSET_PLATE_SHEAR, KEY_OUT_DISP_GUSSET_PLATE_SHEAR, TYPE_TEXTBOX,
        #        self.shear_capacity_gusset if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t26)
        #
        # t27 = (KEY_OUT_GUSSET_PLATE_MOMENT_DEMAND, KEY_OUT_DISP_GUSSET_PLATE_MOMENT_DEMAND, TYPE_TEXTBOX,
        #        self.moment_on_gusset if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t27)
        #
        # t28 = (KEY_OUT_GUSSET_PLATE_MOMENT, KEY_OUT_DISP_GUSSET_PLATE_MOMENT, TYPE_TEXTBOX,
        #        self.moment_capacity_gusset if flag and self.stiffener_along_flange == 'Yes' else '')
        # out_list.append(t28)

        t29 = (None, DISP_TITLE_STIFFENER_PLATE_ALONG_WEB, TYPE_TITLE, None)
        out_list.append(t29)

        t30 = (KEY_OUT_STIFFENER_PLATE_ALONG_WEB, KEY_DISP_OUT_STIFFENER_PLATE_ALONG_WEB, TYPE_OUT_BUTTON,
               ['Stiffener Details', self.stiffener_along_web_details])
        out_list.append(t30)

        t29 = (None, DISP_TITLE_STIFFENER_PLATE_ACROSS_WEB, TYPE_TITLE, None)
        out_list.append(t29)

        t30 = (KEY_OUT_STIFFENER_PLATE_ACROSS_WEB, KEY_DISP_OUT_STIFFENER_PLATE_ACROSS_WEB, TYPE_OUT_BUTTON,
               ['Stiffener Details', self.stiffener_across_web_details])
        out_list.append(t30)

        # t30 = (KEY_OUT_STIFFENER_PLATE_WEB_THICKNNESS, KEY_OUT_DISP_STIFFENER_PLATE_WEB_THICKNESS, TYPE_TEXTBOX,
        #        self.stiffener_plt_thick_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t30)
        #
        # t31 = (KEY_OUT_STIFFENER_PLATE_WEB_SHEAR_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_WEB_SHEAR_DEMAND, TYPE_TEXTBOX,
        #        self.shear_on_stiffener_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t31)
        #
        # t32 = (KEY_OUT_STIFFENER_PLATE_WEB_SHEAR, KEY_OUT_DISP_STIFFENER_PLATE_WEB_SHEAR, TYPE_TEXTBOX,
        #        self.shear_capa_stiffener_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t32)
        #
        # t33 = (KEY_OUT_STIFFENER_PLATE_WEB_MOMENT_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_WEB_MOMENT_DEMAND, TYPE_TEXTBOX,
        #        self.moment_on_stiffener_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t33)
        #
        # t34 = (KEY_OUT_STIFFENER_PLATE_WEB_MOMENT, KEY_OUT_DISP_STIFFENER_PLATE_WEB_MOMENT, TYPE_TEXTBOX,
        #        self.moment_capa_stiffener_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t34)

        # t29 = (None, DISP_TITLE_STIFFENER_PLATE, TYPE_TITLE, None)
        # out_list.append(t29)
        #
        # t30 = (KEY_OUT_STIFFENER_PLATE_THICKNNESS, KEY_OUT_DISP_STIFFENER_PLATE_THICKNESS, TYPE_TEXTBOX,
        #        self.stiffener_plate_thick if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t30)
        #
        # t31 = (KEY_OUT_STIFFENER_PLATE_SHEAR_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_SHEAR_DEMAND, TYPE_TEXTBOX,
        #        self.shear_on_stiffener if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t31)
        #
        # t32 = (KEY_OUT_STIFFENER_PLATE_SHEAR, KEY_OUT_DISP_STIFFENER_PLATE_SHEAR, TYPE_TEXTBOX,
        #        self.shear_capacity_stiffener if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t32)
        #
        # t33 = (KEY_OUT_STIFFENER_PLATE_MOMENT_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_MOMENT_DEMAND, TYPE_TEXTBOX,
        #        self.moment_on_stiffener if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t33)
        #
        # t34 = (KEY_OUT_STIFFENER_PLATE_MOMENT, KEY_OUT_DISP_STIFFENER_PLATE_MOMENT, TYPE_TEXTBOX,
        #        self.moment_capacity_stiffener if flag and self.stiffener_along_web == 'Yes' else '')
        # out_list.append(t34)

        t18 = (None, DISP_TITLE_WELD, TYPE_TITLE, None)
        out_list.append(t18)

        # t19 = (KEY_OUT_WELD_SIZE, DISP_TITLE_WELD, TYPE_OUT_BUTTON, ['Weld Details', self.weld_details])
        # out_list.append(t19)

        # t19 = (KEY_OUT_WELD_SIZE, KEY_OUT_DISP_WELD_SIZE, TYPE_TEXTBOX,
        #        self.weld_size if flag and self.weld_type != 'Butt Weld' else '')
        # out_list.append(t19)

        t20 = (KEY_OUT_WELD_SIZE_FLANGE, KEY_OUT_DISP_WELD_SIZE_FLANGE, TYPE_TEXTBOX,
               self.weld_size_flange if flag and self.weld_type != 'Butt Weld' else '')
        out_list.append(t20)

        t21 = (KEY_OUT_WELD_SIZE_WEB, KEY_OUT_DISP_WELD_SIZE_WEB, TYPE_TEXTBOX,
               self.weld_size_web if flag and self.weld_type != 'Butt Weld' else '')
        out_list.append(t21)

        t22 = (KEY_OUT_WELD_SIZE_STIFFENER, KEY_OUT_DISP_WELD_SIZE_STIFFENER, TYPE_TEXTBOX,
               self.weld_size_stiffener if flag and self.weld_type != 'Butt Weld' and self.gusset_along_flange == 'Yes' else '')
        out_list.append(t22)

        t19 = (KEY_OUT_WELD_SIZE, DISP_TITLE_WELD, TYPE_OUT_BUTTON, ['Weld Details', self.weld_details])
        out_list.append(t19)

        return out_list

    def stiffener_flange_details(self, flag):
        sf = []

        t24 = (KEY_OUT_STIFFENER_PLATE_FLANGE_THICKNNESS, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_THICKNESS, TYPE_TEXTBOX,
               self.stiffener_plt_thick_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        sf.append(t24)

        t25 = (KEY_OUT_STIFFENER_PLATE_FLANGE_SHEAR_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_SHEAR_DEMAND,
               TYPE_TEXTBOX,
               self.shear_on_stiffener_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        sf.append(t25)

        t26 = (KEY_OUT_STIFFENER_PLATE_FLANGE_SHEAR, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_SHEAR, TYPE_TEXTBOX,
               self.shear_capa_stiffener_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        sf.append(t26)

        t27 = (KEY_OUT_STIFFENER_PLATE_FLANGE_MOMENT_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_MOMENT_DEMAND,
               TYPE_TEXTBOX,
               self.moment_on_stiffener_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        sf.append(t27)

        t28 = (KEY_OUT_STIFFENER_PLATE_FLANGE_MOMENT, KEY_OUT_DISP_STIFFENER_PLATE_FLANGE_MOMENT, TYPE_TEXTBOX,
               self.moment_capa_stiffener_along_flange if flag and self.stiffener_along_flange == 'Yes' else '')
        sf.append(t28)

        return sf

    def stiffener_along_web_details(self, flag):

        sw = []

        t30 = (KEY_OUT_STIFFENER_PLATE_ALONG_WEB_THICKNNESS, KEY_OUT_DISP_STIFFENER_PLATE_ALONG_WEB_THICKNESS, TYPE_TEXTBOX,
               self.stiffener_plt_thick_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        sw.append(t30)

        t31 = (KEY_OUT_STIFFENER_PLATE_ALONG_WEB_SHEAR_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_ALONG_WEB_SHEAR_DEMAND, TYPE_TEXTBOX,
               self.shear_on_stiffener_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        sw.append(t31)

        t32 = (KEY_OUT_STIFFENER_PLATE_ALONG_WEB_SHEAR, KEY_OUT_DISP_STIFFENER_PLATE_ALONG_WEB_SHEAR, TYPE_TEXTBOX,
               self.shear_capa_stiffener_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        sw.append(t32)

        t33 = (KEY_OUT_STIFFENER_PLATE_ALONG_WEB_MOMENT_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_ALONG_WEB_MOMENT_DEMAND, TYPE_TEXTBOX,
               self.moment_on_stiffener_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        sw.append(t33)

        t34 = (KEY_OUT_STIFFENER_PLATE_ALONG_WEB_MOMENT, KEY_OUT_DISP_STIFFENER_PLATE_ALONG_WEB_MOMENT, TYPE_TEXTBOX,
               self.moment_capa_stiffener_along_web if flag and self.stiffener_along_web == 'Yes' else '')
        sw.append(t34)

        return sw

    def stiffener_across_web_details(self, flag):

        sw = []

        t30 = (KEY_OUT_STIFFENER_PLATE_ACROSS_WEB_THICKNNESS, KEY_OUT_DISP_STIFFENER_PLATE_ACROSS_WEB_THICKNESS, TYPE_TEXTBOX,
               self.stiffener_plt_thick_across_web if flag and self.stiffener_across_web == 'Yes' else '')
        sw.append(t30)

        t31 = (KEY_OUT_STIFFENER_PLATE_ACROSS_WEB_SHEAR_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_ACROSS_WEB_SHEAR_DEMAND, TYPE_TEXTBOX,
               self.shear_on_stiffener_across_web if flag and self.stiffener_across_web == 'Yes' else '')
        sw.append(t31)

        t32 = (KEY_OUT_STIFFENER_PLATE_ACROSS_WEB_SHEAR, KEY_OUT_DISP_STIFFENER_PLATE_ACROSS_WEB_SHEAR, TYPE_TEXTBOX,
               self.shear_capa_stiffener_across_web if flag and self.stiffener_across_web == 'Yes' else '')
        sw.append(t32)

        t33 = (KEY_OUT_STIFFENER_PLATE_ACROSS_WEB_MOMENT_DEMAND, KEY_OUT_DISP_STIFFENER_PLATE_ACROSS_WEB_MOMENT_DEMAND, TYPE_TEXTBOX,
               self.moment_on_stiffener_across_web if flag and self.stiffener_across_web == 'Yes' else '')
        sw.append(t33)

        t34 = (KEY_OUT_STIFFENER_PLATE_ACROSS_WEB_MOMENT, KEY_OUT_DISP_STIFFENER_PLATE_ACROSS_WEB_MOMENT, TYPE_TEXTBOX,
               self.moment_capa_stiffener_across_web if flag and self.stiffener_across_web == 'Yes' else '')
        sw.append(t34)

        return sw

    def weld_details(self, flag):

        weld = []

        t99 = (None, '', TYPE_IMAGE, './ResourceFiles/images/Butt_weld_double_bevel_flange.png')
        weld.append(t99)

        t99 = (None, '', TYPE_IMAGE, './ResourceFiles/images/Butt_weld_double_bevel_web.png')
        weld.append(t99)

        return weld

    def major_minor(self):
        if self in ['Welded+Bolted Column Base', 'Moment Base Plate', 'Hollow/Tubular Column Base']:
            return True
        else:
            return False

    def conn_axial_tension(self):
        if self == 'Moment Base Plate':
            return True
        else:
            return False

    def label_end_condition(self):
        if self in ['Moment Base Plate', 'Hollow/Tubular Column Base']:
            return 'Fixed'
        else:
            return 'Pinned'

    def anchor_type_warning(self):

        if self in ['IS 5624-Type A', 'IS 5624-Type B']:
            return True
        else:
            return False

    def conn_weld_type(self):
        if self in ['Welded+Bolted Column Base', 'Hollow/Tubular Column Base']:
            return VALUES_WELD_TYPE
        else:
            weld = []
            weld.append(VALUES_WELD_TYPE[0])
            weld.append(VALUES_WELD_TYPE[2])
            return weld

    def out_weld(self):
        if self == 'Butt Weld':
            return True
        else:
            return False

    def out_anchor_tension(self):
        if self != 'Moment Base Plate':
            return True
        else:
            return False

    def out_detail_projection(self):
        if self != 'Welded Column Base':
            return True
        else:
            return False

    def out_anchor_combined(self):
        if self != 'Welded Column Base':
            return True
        else:
            return False

    def input_value_changed(self):

        lst = []

        t1 = (KEY_CONN, KEY_MOMENT_MAJOR, TYPE_TEXTBOX, self.major_minor)
        lst.append(t1)

        t2 = (KEY_CONN, KEY_MOMENT_MINOR, TYPE_TEXTBOX, self.major_minor)
        lst.append(t2)

        t19 = (KEY_CONN, KEY_AXIAL_TENSION_BP, TYPE_TEXTBOX, self.conn_axial_tension)
        lst.append(t19)

        t3 = (KEY_CONN, KEY_END_CONDITION, TYPE_NOTE, self.label_end_condition)
        lst.append(t3)

        # t4 = (KEY_WELD_TYPE, KEY_OUT_WELD_SIZE, TYPE_OUT_DOCK, self.out_weld)
        # lst.append(t4)
        #
        # t5 = (KEY_WELD_TYPE, KEY_OUT_WELD_SIZE, TYPE_OUT_LABEL, self.out_weld)
        # lst.append(t5)

        t18 = (KEY_TYP_ANCHOR,
               'The selected anchor bolt type is not suggested by Osdag due to its less on field acceptance and '
               'availability in the market.', TYPE_WARNING, self.anchor_type_warning)
        lst.append(t18)

        t20 = (KEY_CONN, KEY_WELD_TYPE, TYPE_COMBOBOX, self.conn_weld_type)
        lst.append(t20)

        t12 = (KEY_WELD_TYPE, KEY_OUT_WELD_SIZE_FLANGE, TYPE_OUT_DOCK, self.out_weld)
        lst.append(t12)

        t13 = (KEY_WELD_TYPE, KEY_OUT_WELD_SIZE_FLANGE, TYPE_OUT_LABEL, self.out_weld)
        lst.append(t13)

        t14 = (KEY_WELD_TYPE, KEY_OUT_WELD_SIZE_WEB, TYPE_OUT_DOCK, self.out_weld)
        lst.append(t14)

        t15 = (KEY_WELD_TYPE, KEY_OUT_WELD_SIZE_WEB, TYPE_OUT_LABEL, self.out_weld)
        lst.append(t15)

        t16 = (KEY_WELD_TYPE, KEY_OUT_WELD_SIZE_STIFFENER, TYPE_OUT_DOCK, self.out_weld)
        lst.append(t16)

        t17 = (KEY_WELD_TYPE, KEY_OUT_WELD_SIZE_STIFFENER, TYPE_OUT_LABEL, self.out_weld)
        lst.append(t17)

        t6 = (KEY_CONN, KEY_OUT_ANCHOR_BOLT_TENSION, TYPE_OUT_DOCK, self.out_anchor_tension)
        lst.append(t6)

        t7 = (KEY_CONN, KEY_OUT_ANCHOR_BOLT_TENSION, TYPE_OUT_LABEL, self.out_anchor_tension)
        lst.append(t7)

        t8 = (KEY_CONN, KEY_OUT_DETAILING_PROJECTION, TYPE_OUT_DOCK, self.out_detail_projection)
        lst.append(t8)

        t9 = (KEY_CONN, KEY_OUT_DETAILING_PROJECTION, TYPE_OUT_LABEL, self.out_detail_projection)
        lst.append(t9)

        t10 = (KEY_CONN, KEY_OUT_ANCHOR_BOLT_COMBINED, TYPE_OUT_DOCK, self.out_anchor_combined)
        lst.append(t10)

        t11 = (KEY_CONN, KEY_OUT_ANCHOR_BOLT_COMBINED, TYPE_OUT_LABEL, self.out_anchor_combined)
        lst.append(t11)

        t12 = (KEY_CONN, KEY_OUT_DIA_ANCHOR_UPLIFT, TYPE_OUT_DOCK, self.out_anchor_tension)
        lst.append(t12)

        t13 = (KEY_CONN, KEY_OUT_DIA_ANCHOR_UPLIFT, TYPE_OUT_LABEL, self.out_anchor_tension)
        lst.append(t13)

        t14 = (KEY_CONN, KEY_OUT_GRD_ANCHOR_UPLIFT, TYPE_OUT_DOCK, self.out_anchor_tension)
        lst.append(t14)

        t15 = (KEY_CONN, KEY_OUT_GRD_ANCHOR_UPLIFT, TYPE_OUT_LABEL, self.out_anchor_tension)
        lst.append(t15)

        t16 = (KEY_CONN, KEY_OUT_ANCHOR_BOLT_LENGTH_UPLIFT, TYPE_OUT_DOCK, self.out_anchor_tension)
        lst.append(t16)

        t17 = (KEY_CONN, KEY_OUT_ANCHOR_BOLT_LENGTH_UPLIFT, TYPE_OUT_LABEL, self.out_anchor_tension)
        lst.append(t17)

        t18 = (KEY_CONN, KEY_OUT_ANCHOR_BOLT_TENSION_UPLIFT, TYPE_OUT_DOCK, self.out_anchor_tension)
        lst.append(t18)

        t19 = (KEY_CONN, KEY_OUT_ANCHOR_BOLT_TENSION_UPLIFT, TYPE_OUT_LABEL, self.out_anchor_tension)
        lst.append(t19)

        return lst

    @staticmethod
    def diam_bolt_customized():
        c = connectdb2()
        return c

    @staticmethod
    def grdval_customized():
        b = VALUES_GRD_CUSTOMIZED
        return b

    def customized_input(self):

        list1 = []
        t1 = (KEY_DIA_ANCHOR, self.diam_bolt_customized)
        list1.append(t1)
        t2 = (KEY_GRD_ANCHOR, self.grdval_customized)
        list1.append(t2)

        return list1

    def func_for_validation(self, design_dictionary):
        all_errors = []
        self.design_status = False
        flag = False
        option_list = self.input_values(self)
        missing_fields_list = []
        if design_dictionary[KEY_CONN] == 'Welded Column Base':
            design_dictionary[KEY_MOMENT_MAJOR] = 'Disabled'
            design_dictionary[KEY_MOMENT_MINOR] = 'Disabled'
        if design_dictionary[KEY_CONN] != 'Moment Base Plate' or design_dictionary[KEY_AXIAL_TENSION_BP] == '':
            design_dictionary[KEY_AXIAL_TENSION_BP] = 'Disabled'
        if design_dictionary[KEY_SHEAR_MAJOR] == '':
            design_dictionary[KEY_SHEAR_MAJOR] = '0'
        if design_dictionary[KEY_SHEAR_MINOR] == '':
            design_dictionary[KEY_SHEAR_MINOR] = '0'
        for option in option_list:
            if option[2] == TYPE_TEXTBOX:
                if design_dictionary[option[0]] == '':
                    missing_fields_list.append(option[1])
            elif option[2] == TYPE_COMBOBOX and option[0] != KEY_CONN:
                val = option[4]
                if design_dictionary[option[0]] == val[0]:
                    missing_fields_list.append(option[1])
            elif option[2] == TYPE_COMBOBOX_CUSTOMIZED:
                if design_dictionary[option[0]] == []:
                    missing_fields_list.append(option[1])

        if len(missing_fields_list) > 0:
            error = self.generate_missing_fields_error_string(self,missing_fields_list)
            all_errors.append(error)
            # flag = False
        else:
            flag = True

        if flag:
            print(design_dictionary)
            # self.set_input_values(self, design_dictionary)
            self.bp_parameters(self, design_dictionary)
        else:
            return all_errors

    def generate_missing_fields_error_string(self, missing_fields_list):
        """
        Args:
            missing_fields_list: list of fields that are not selected or entered
        Returns:
            error string that has to be displayed
        """
        # The base string which should be displayed
        information = "Please input the following required field"
        if len(missing_fields_list) > 1:
            # Adds 's' to the above sentence if there are multiple missing input fields
            information += "s"
        information += ": "
        # Loops through the list of the missing fields and adds each field to the above sentence with a comma

        for item in missing_fields_list:
            information = information + item + ", "

        # Removes the last comma
        information = information[:-2]
        information += "."

        return information


    def tab_list(self):
        self.design_button_status = False

        tabs = []

        t0 = (KEY_DISP_COLSEC, TYPE_TAB_1, self.tab_column_section)
        tabs.append(t0)

        t5 = ("Base Plate", TYPE_TAB_2, self.tab_bp)
        tabs.append(t5)

        t1 = ("Anchor Bolt", TYPE_TAB_2, self.anchor_bolt_values)
        tabs.append(t1)

        t2 = ("Weld", TYPE_TAB_2, self.weld_values)
        tabs.append(t2)

        t3 = ("Detailing", TYPE_TAB_2, self.detailing_values)
        tabs.append(t3)

        t4 = ("Design", TYPE_TAB_2, self.design_values)
        tabs.append(t4)

        # t5 = ("Connector", TYPE_TAB_2, self.connector_values)
        # tabs.append(t5)

        return tabs

    @staticmethod
    def anchor_bolt_values():
        anchor_bolt = []

        t1 = (KEY_DP_ANCHOR_BOLT_DESIGNATION, KEY_DISP_DESIGNATION, TYPE_TEXTBOX, '')
        anchor_bolt.append(t1)

        t2 = (KEY_DP_ANCHOR_BOLT_TYPE, KEY_DISP_DP_ANCHOR_BOLT_TYPE, TYPE_TEXTBOX, '')
        anchor_bolt.append(t2)

        t3 = (KEY_DP_ANCHOR_BOLT_GALVANIZED, KEY_DISP_DP_ANCHOR_BOLT_GALVANIZED, TYPE_COMBOBOX, ['Yes', 'No'])
        anchor_bolt.append(t3)

        t4 = (
            KEY_DP_ANCHOR_BOLT_HOLE_TYPE, KEY_DISP_DP_ANCHOR_BOLT_HOLE_TYPE, TYPE_COMBOBOX, ['Standard', 'Over-sized'])
        anchor_bolt.append(t4)

        t5 = (KEY_DP_ANCHOR_BOLT_LENGTH, KEY_DISP_DP_ANCHOR_BOLT_LENGTH, TYPE_TEXTBOX, '')
        anchor_bolt.append(t5)

        t6 = (KEY_DP_ANCHOR_BOLT_MATERIAL_G_O, KEY_DISP_DP_ANCHOR_BOLT_MATERIAL_G_O, TYPE_TEXTBOX, '')
        anchor_bolt.append(t6)

        t7 = (KEY_DP_ANCHOR_BOLT_FRICTION, KEY_DISP_DP_ANCHOR_BOLT_FRICTION, TYPE_TEXTBOX, '0.30')
        anchor_bolt.append(t7)

        return anchor_bolt

    @staticmethod
    def tab_bp():
        tab_bp = []
        t1 = (KEY_BASE_PLATE_MATERIAL, KEY_DISP_BASE_PLATE_MATERIAL, TYPE_TEXTBOX, None)
        tab_bp.append(t1)

        t2 = (KEY_BASE_PLATE_FU, KEY_DISP_BASE_PLATE_FU, TYPE_TEXTBOX, None)
        tab_bp.append(t2)

        t3 = (KEY_BASE_PLATE_FY, KEY_DSIP_BASE_PLATE_FY, TYPE_TEXTBOX, None)
        tab_bp.append(t3)

        return tab_bp

    @staticmethod
    def detailing_values():
        detailing = []

        t1 = (KEY_DP_DETAILING_EDGE_TYPE, KEY_DISP_DP_DETAILING_EDGE_TYPE, TYPE_COMBOBOX, [
            'a - Sheared or hand flame cut', 'b - Rolled, machine-flame cut, sawn and planed'])
        detailing.append(t1)

        t3 = (KEY_DP_DETAILING_CORROSIVE_INFLUENCES, KEY_DISP_DP_DETAILING_CORROSIVE_INFLUENCES, TYPE_COMBOBOX,
              ['No', 'Yes'])
        detailing.append(t3)

        t4 = ["textBrowser", "", TYPE_TEXT_BROWSER, DETAILING_DESCRIPTION]
        detailing.append(t4)

        return detailing

    @staticmethod
    def design_values():

        design = []

        t1 = (KEY_DP_DESIGN_METHOD, KEY_DISP_DP_DESIGN_METHOD, TYPE_COMBOBOX, ['Limit State Design',
                                                                               'Limit State (Capacity based) Design',
                                                                               'Working Stress Design'])
        design.append(t1)

        t2 = (KEY_DP_DESIGN_BASE_PLATE, KEY_DISP_DP_DESIGN_BASE_PLATE, TYPE_COMBOBOX, ['Effective Area Method'])
        design.append(t2)

        return design

    @staticmethod
    def tab_column_section():
        supporting_section = []
        t1 = (KEY_SUPTNGSEC_DESIGNATION, KEY_DISP_SUPTNGSEC_DESIGNATION, TYPE_TEXTBOX, None)
        supporting_section.append(t1)

        t2 = (None, KEY_DISP_MECH_PROP, TYPE_TITLE, None)
        supporting_section.append(t2)

        # material = connectdb("Material", call_type="popup")
        # material.append('Custom')
        t34 = (KEY_SUPTNGSEC_MATERIAL, KEY_DISP_MATERIAL, TYPE_TEXTBOX, None)
        supporting_section.append(t34)

        # t3 = (KEY_SUPTNGSEC_FU, KEY_DISP_SUPTNGSEC_FU, TYPE_TEXTBOX, None)
        # supporting_section.append(t3)

        # t4 = (KEY_SUPTNGSEC_FY, KEY_DISP_SUPTNGSEC_FY, TYPE_TEXTBOX, None)
        # supporting_section.append(t4)

        t5 = (None, KEY_DISP_DIMENSIONS, TYPE_TITLE, None)
        supporting_section.append(t5)

        t6 = (KEY_SUPTNGSEC_DEPTH, KEY_DISP_SUPTNGSEC_DEPTH, TYPE_TEXTBOX, None)
        supporting_section.append(t6)

        t7 = (KEY_SUPTNGSEC_FLANGE_W, KEY_DISP_SUPTNGSEC_FLANGE_W, TYPE_TEXTBOX, None)
        supporting_section.append(t7)

        t8 = (KEY_SUPTNGSEC_FLANGE_T, KEY_DISP_SUPTNGSEC_FLANGE_T, TYPE_TEXTBOX, None)
        supporting_section.append(t8)

        t9 = (KEY_SUPTNGSEC_WEB_T, KEY_DISP_SUPTNGSEC_WEB_T, TYPE_TEXTBOX, None)
        supporting_section.append(t9)

        t10 = (KEY_SUPTNGSEC_FLANGE_S, KEY_DISP_SUPTNGSEC_FLANGE_S, TYPE_TEXTBOX, None)
        supporting_section.append(t10)

        t11 = (KEY_SUPTNGSEC_ROOT_R, KEY_DISP_SUPTNGSEC_ROOT_R, TYPE_TEXTBOX, None)
        supporting_section.append(t11)

        t12 = (KEY_SUPTNGSEC_TOE_R, KEY_DISP_SUPTNGSEC_TOE_R, TYPE_TEXTBOX, None)
        supporting_section.append(t12)

        t13 = (None, None, TYPE_BREAK, None)
        supporting_section.append(t13)

        t14 = (KEY_SUPTNGSEC_TYPE, KEY_DISP_SUPTNGSEC_TYPE, TYPE_COMBOBOX, ['Rolled', 'Welded'])
        supporting_section.append(t14)

        # t18 = (None, None, TYPE_ENTER, None)
        # supporting_section.append(t18)

        t18 = (None, None, TYPE_ENTER, None)
        supporting_section.append(t18)

        t3 = (KEY_SUPTNGSEC_FU, KEY_DISP_SUPTNGSEC_FU, TYPE_TEXTBOX, None)
        supporting_section.append(t3)

        # t15 = (KEY_SUPTNGSEC_MOD_OF_ELAST, KEY_SUPTNGSEC_DISP_MOD_OF_ELAST, TYPE_TEXTBOX, None)
        # supporting_section.append(t15)
        #
        # t16 = (KEY_SUPTNGSEC_MOD_OF_RIGID, KEY_SUPTNGSEC_DISP_MOD_OF_RIGID, TYPE_TEXTBOX, None)
        # supporting_section.append(t16)

        t17 = (None, KEY_DISP_SEC_PROP, TYPE_TITLE, None)
        supporting_section.append(t17)

        t18 = (KEY_SUPTNGSEC_MASS, KEY_DISP_SUPTNGSEC_MASS, TYPE_TEXTBOX, None)
        supporting_section.append(t18)

        t19 = (KEY_SUPTNGSEC_SEC_AREA, KEY_DISP_SUPTNGSEC_SEC_AREA, TYPE_TEXTBOX, None)
        supporting_section.append(t19)

        t20 = (KEY_SUPTNGSEC_MOA_LZ, KEY_DISP_SUPTNGSEC_MOA_LZ, TYPE_TEXTBOX, None)
        supporting_section.append(t20)

        t21 = (KEY_SUPTNGSEC_MOA_LY, KEY_DISP_SUPTNGSEC_MOA_LY, TYPE_TEXTBOX, None)
        supporting_section.append(t21)

        t22 = (KEY_SUPTNGSEC_ROG_RZ, KEY_DISP_SUPTNGSEC_ROG_RZ, TYPE_TEXTBOX, None)
        supporting_section.append(t22)

        t23 = (KEY_SUPTNGSEC_ROG_RY, KEY_DISP_SUPTNGSEC_ROG_RY, TYPE_TEXTBOX, None)
        supporting_section.append(t23)

        t24 = (KEY_SUPTNGSEC_EM_ZZ, KEY_DISP_SUPTNGSEC_EM_ZZ, TYPE_TEXTBOX, None)
        supporting_section.append(t24)

        t25 = (KEY_SUPTNGSEC_EM_ZY, KEY_DISP_SUPTNGSEC_EM_ZY, TYPE_TEXTBOX, None)
        supporting_section.append(t25)

        t26 = (KEY_SUPTNGSEC_PM_ZPZ, KEY_DISP_SUPTNGSEC_PM_ZPZ, TYPE_TEXTBOX, None)
        supporting_section.append(t26)

        t27 = (KEY_SUPTNGSEC_PM_ZPY, KEY_DISP_SUPTNGSEC_PM_ZPY, TYPE_TEXTBOX, None)
        supporting_section.append(t27)

        t28 = (None, None, TYPE_BREAK, None)
        supporting_section.append(t28)

        t29 = (KEY_SUPTNGSEC_SOURCE, KEY_DISP_SUPTNGSEC_SOURCE, TYPE_TEXTBOX, None)
        supporting_section.append(t29)

        # t30 = (None, None, TYPE_ENTER, None)
        # supporting_section.append(t30)

        t30 = (None, None, TYPE_ENTER, None)
        supporting_section.append(t30)

        t4 = (KEY_SUPTNGSEC_FY, KEY_DISP_SUPTNGSEC_FY, TYPE_TEXTBOX, None)
        supporting_section.append(t4)

        # t31 = (KEY_SUPTNGSEC_POISSON_RATIO, KEY_DISP_SUPTNGSEC_POISSON_RATIO, TYPE_TEXTBOX, None)
        # supporting_section.append(t31)
        #
        # t32 = (KEY_SUPTNGSEC_THERMAL_EXP, KEY_DISP_SUPTNGSEC_THERMAL_EXP, TYPE_TEXTBOX, None)
        # supporting_section.append(t32)

        t33 = (KEY_IMAGE, None, TYPE_IMAGE, None, None)
        supporting_section.append(t33)

        return supporting_section

    # def dia_to_len(self, d):
    #
    #     ob = IS_5624_1993()
    #     l = ob.table1(d)
    #     return l

    # Start of calculation

    def bp_parameters(self, design_dictionary):
        """ Initialize variables to use in calculation from input dock and design preference UI.

        Args: design dictionary based on the user inputs from the GUI

        Returns: None
        """
        # attributes of input dock
        self.mainmodule = "Moment Connection"
        self.connectivity = str(design_dictionary[KEY_CONN])
        self.end_condition = str(design_dictionary[KEY_END_CONDITION])
        self.column_section = str(design_dictionary[KEY_SUPTNGSEC])
        self.material = str(design_dictionary[KEY_MATERIAL])

        self.load_axial_compression = float(design_dictionary[KEY_AXIAL_BP])
        self.load_axial_compression = self.load_axial_compression * 10 ** 3  # N

        self.load_axial_tension = float(design_dictionary[KEY_AXIAL_TENSION_BP] if design_dictionary[KEY_AXIAL_TENSION_BP] != 'Disabled' else 0)
        self.load_axial_tension = self.load_axial_tension * 10 ** 3  # N

        # self.load_shear = float(design_dictionary[KEY_SHEAR_BP])
        # self.load_shear = self.load_shear * 10 ** 3  # N

        self.load_shear_major = float(design_dictionary[KEY_SHEAR_MAJOR])  # shear force acting along the major axis
        self.load_shear_major = self.load_shear_major * 10 ** 3  # N

        self.load_shear_minor = float(design_dictionary[KEY_SHEAR_MINOR])  # shear force acting along the minor axis
        self.load_shear_minor = self.load_shear_minor * 10 ** 3  # N

        # TODO: check the condition given below
        # if self.load_shear_major < self.load_shear_minor:
        #     self.load_shear_major = self.load_shear_minor
        # else:
        #     pass

        self.load_moment_major = float(design_dictionary[KEY_MOMENT_MAJOR]
                                       if design_dictionary[KEY_MOMENT_MAJOR] != 'Disabled' else 0)  # bending moment acting about the major axis
        self.load_moment_major = self.load_moment_major * 10 ** 6  # N-mm

        self.load_moment_minor = float(design_dictionary[KEY_MOMENT_MINOR]
                                       if design_dictionary[KEY_MOMENT_MINOR] != 'Disabled' else 0) # bending moment acting about the minor axis
        self.load_moment_minor = self.load_moment_minor * 10 ** 6  # N-mm

        # checking if the user input for minor axis moment exceeds the major axis moment (practically, it shouldn't)
        if self.load_moment_major < self.load_moment_minor:
            self.load_moment_major = self.load_moment_minor  # designing for maximum moment
        else:
            pass

        self.anchor_dia = design_dictionary[KEY_DIA_ANCHOR]
        self.anchor_type = str(design_dictionary[KEY_TYP_ANCHOR])
        self.anchor_grade = design_dictionary[KEY_GRD_ANCHOR]
        self.anchor_grade_tension = self.anchor_grade

        self.footing_grade = str(design_dictionary[KEY_GRD_FOOTING])

        self.weld_type = str(design_dictionary[KEY_WELD_TYPE])

        # attributes of design preferences
        self.dp_column_designation = str(design_dictionary[KEY_SUPTNGSEC])
        self.dp_column_type = str(design_dictionary[KEY_SUPTNGSEC_TYPE])
        self.dp_column_source = str(design_dictionary[KEY_SUPTNGSEC_SOURCE])
        self.dp_column_material = str(design_dictionary[KEY_SUPTNGSEC_MATERIAL])
        self.dp_column_fu = float(design_dictionary[KEY_SUPTNGSEC_FU])
        self.dp_column_fy = float(design_dictionary[KEY_SUPTNGSEC_FY])

        self.dp_bp_material = str(design_dictionary[KEY_BASE_PLATE_MATERIAL])
        self.dp_bp_fu = float(design_dictionary[KEY_BASE_PLATE_FU])
        self.dp_bp_fy = float(design_dictionary[KEY_BASE_PLATE_FY])

        self.dp_anchor_designation = str(design_dictionary[KEY_DP_ANCHOR_BOLT_DESIGNATION])
        self.dp_anchor_type = str(design_dictionary[KEY_DP_ANCHOR_BOLT_TYPE])
        self.dp_anchor_hole = str(design_dictionary[KEY_DP_ANCHOR_BOLT_HOLE_TYPE])
        self.dp_anchor_length = float(design_dictionary[KEY_DP_ANCHOR_BOLT_LENGTH])
        self.dp_anchor_fu_overwrite = float(design_dictionary[KEY_DP_ANCHOR_BOLT_MATERIAL_G_O])
        self.dp_anchor_friction = float(design_dictionary[KEY_DP_ANCHOR_BOLT_FRICTION] if
                                        design_dictionary[KEY_DP_ANCHOR_BOLT_FRICTION] != "" else 0.30)

        self.dp_weld_fab = str(design_dictionary[KEY_DP_WELD_FAB])
        self.dp_weld_fu_overwrite = float(design_dictionary[KEY_DP_WELD_MATERIAL_G_O])

        self.dp_detail_edge_type = str(design_dictionary[KEY_DP_DETAILING_EDGE_TYPE])
        self.dp_detail_is_corrosive = str(design_dictionary[KEY_DP_DETAILING_CORROSIVE_INFLUENCES])

        self.dp_design_method = str(design_dictionary[KEY_DP_DESIGN_METHOD])
        self.dp_bp_method = str(design_dictionary[KEY_DP_DESIGN_BASE_PLATE])

        # properties of the column section

        self.column_properties = Column(designation=self.dp_column_designation, material_grade=self.dp_column_material)
        self.column_D = self.column_properties.depth
        self.column_bf = self.column_properties.flange_width
        self.column_tf = self.column_properties.flange_thickness
        self.column_tw = self.column_properties.web_thickness
        self.column_r1 = self.column_properties.root_radius
        self.column_r2 = self.column_properties.toe_radius

        # other attributes
        self.gamma_m0 = self.cl_5_4_1_Table_5["gamma_m0"]["yielding"]  # gamma_mo = 1.10
        self.gamma_m1 = self.cl_5_4_1_Table_5["gamma_m1"]["ultimate_stress"]  # gamma_m1 = 1.25
        self.gamma_mb = self.cl_5_4_1_Table_5["gamma_mb"][self.dp_weld_fab]  # gamma_mb = 1.25
        self.gamma_mw = self.cl_5_4_1_Table_5["gamma_mw"][self.dp_weld_fab]  # gamma_mw = 1.25 for 'Shop Weld' and 1.50 for 'Field Weld'

        self.safe = True

        self.stiffener_plt_thick_along_flange = 0.0
        self.stiffener_plt_thick_along_web = 0.0
        self.stiffener_plt_thick_across_web = 0.0
        self.stiffener_plt_height_along_flange = 0.0
        self.stiffener_plt_height_along_web = 0.0
        self.stiffener_plt_height_across_web = 0.0

        self.shear_on_stiffener_along_flange = 0.0
        self.shear_capa_stiffener_along_flange = 0.0
        self.moment_on_stiffener_along_flange = 0.0
        self.moment_capa_stiffener_along_flange = 0.0
        self.z_e_stiffener_along_flange = 0.0

        self.shear_on_stiffener_along_web = 0.0
        self.shear_capa_stiffener_along_web = 0.0
        self.moment_on_stiffener_along_web = 0.0
        self.moment_capa_stiffener_along_web = 0.0
        self.z_e_stiffener_along_web = 0.0

        self.weld_size_flange = 0.0
        self.weld_size_web = 0.0
        self.gusset_along_flange = 'No'
        self.gusset_along_web = 'No'
        self.gusset_plate_length = 0.0
        self.stiffener_plate_length = 0.0
        self.total_eff_len_gusset_available = 0.0
        self.gusset_outstand_length = 0.0
        self.stiffener_outstand_length = 0.0
        self.gusset_fy = self.dp_column_fy
        self.stiffener_fy = self.dp_column_fy
        self.epsilon = 1
        self.gusset_plate_thick = 0.0
        self.stiffener_plate_thick = 0.0
        self.gusset_plate_height = 0.0
        self.stiffener_plate_height = 0.0
        self.stiffener_plt_len_along_flange = 0.0
        self.stiffener_plt_len_along_web = 0.0
        self.stiffener_plt_len_across_web = 0.0

        self.weld_size_gusset = 0.0
        self.weld_size_stiffener = 0.0
        self.weld_size_vertical_flange = 0.0
        self.weld_size_vertical_web = 0.0

        self.stiffener_plt_thick_across_web = 0
        self.shear_on_stiffener_across_web = 0
        self.shear_capa_stiffener_across_web = 0
        self.moment_on_stiffener_across_web = 0
        self.moment_capa_stiffener_across_web = 0

        self.bp_analyses_parameters(self)
        print('bp_analyses_parameters done')
        self.bp_analyses(self)
        print('bp_analyses done')
        self.anchor_bolt_design(self)
        print('anchor_bolt_design done')
        self.design_weld(self)
        print('design_weld done')
        self.design_stiffeners(self)
        print('design_stiffeners done')

    def bp_analyses_parameters(self):
        """ initialize detailing parameters like the end/edge/pitch/gauge distances, anchor bolt diameter and grade,
         length and width of the base plate. These parameters are used to run the first iteration of the analyses and improvise accordingly.

        Args:

        Returns:
        """
        # select anchor bolt diameter [Reference: based on design experience, field conditions  and sample calculations]
        # the following list of anchor diameters are neglected due its practical non acceptance/unavailability - 'M8', 'M10', 'M12', 'M16'
        # M20 and M24 are the preferred choices for the design

        # self.anchor_dia = self.anchor_dia
        sort_bolt = filter(lambda x: 'M20' <= x <= self.anchor_dia[-1], self.anchor_dia)

        for i in sort_bolt:
            self.anchor_bolt = i  # anchor dia provided (str)
            break

        self.anchor_dia_provided = self.table1(self.anchor_bolt)[0]  # mm anchor dia provided (int)
        self.anchor_area = self.bolt_area(self.anchor_dia_provided)  # list of areas [shank area, thread area] mm^2

        # hole diameter
        self.anchor_hole_dia = self.cl_10_2_1_bolt_hole_size(self.anchor_dia_provided, self.dp_anchor_hole)  # mm

        # assign anchor grade from the selected list
        # trying the design with the highest selected grade
        self.anchor_grade = list(reversed(self.anchor_grade))
        for i in self.anchor_grade:
            self.anchor_grade = i
            break

        self.anchor_fu_fy = self.get_bolt_fu_fy(self.anchor_grade)  # returns a list with strength values - [bolt_fu, bolt_fy]

        # TODO add condition for number of anchor bolts depending on col depth and force
        # number of anchor bolts outside the column flange
        self.anchor_nos_provided = 4

        # perform detailing checks
        # Note: end distance is along the depth, whereas, the edge distance is along the flange, of the column section

        # end distance [Reference: Clause 10.2.4.2 and 10.2.4.3, IS 800:2007]
        self.end_distance = self.cl_10_2_4_2_min_edge_end_dist(self.anchor_dia_provided, self.dp_anchor_hole, self.dp_detail_edge_type)
        self.end_distance = round_up(1.5 * self.end_distance, 5)  # mm, adding 50% extra to end distance to incorporate weld etc.

        # If the shear force acting along any axis of the column is large (braced frames or buildings designed for seismic forces, heavy winds etc.),
        # the minimum recommended end/edge distance is six times the anchor diameter (min_end_distance = 6 * anchor_diameter).
        # This is to prevent the side bursting/face break-out of the concrete [Reference: AISC Design Guide 1, section 3.2.2, page 22]
        if self.load_shear_major or self.load_shear_minor > 0:
            min_end_distance = 6 * self.anchor_dia_provided  # TODO: check if shear is large enough
            min_end_distance = round_up(min_end_distance, 5)  # mm

            self.end_distance = max(self.end_distance, min_end_distance)
            # TODO: give suitable log messages
        else:
            pass

        # TODO: add max end, edge distance check after the plate thk check
        # self.end_distance_max = self.cl_10_2_4_3_max_edge_dist([self.plate_thk], self.dp_bp_fy, self.dp_detail_is_corrosive)

        # edge distance [Reference: Clause 10.2.4.2 and 10.2.4.3, IS 800:2007]
        self.edge_distance = self.end_distance  # mm
        # self.edge_distance_max = self.end_distance_max

        # pitch and gauge distance [Reference: Clause 10.2.2 and 10.2.3.1, IS 800:2007]
        # TODO add pitch and gauge calc for bolts more than 4 nos
        if self.anchor_nos_provided == 4:
            self.pitch_distance = 0.0
            self.gauge_distance = self.pitch_distance
        else:
            pass

        # minimum required dimensions of the base plate [as per the detailing criteria]
        # considering clearance equal to 1.5 times the edge distance (on each side) along the width of the base plate
        if self.connectivity == 'Welded Column Base' or 'Moment Base Plate':
            self.bp_length_min = round_up(self.column_D + 2 * (2 * self.end_distance), 5)  # mm
            self.bp_width_min = round_up(self.column_bf + 1.5 * self.edge_distance + 1.5 * self.edge_distance, 5)  # mm

        elif self.connectivity == 'Welded+Bolted Column Base':
            pass

        else:
            pass

    def bp_analyses(self):
        """ perform analyses of the base plate

        Args:

        Returns:

        # TODO: Write algorithm here
        """
        # bearing strength of concrete [Reference: Clause 7.4.1, IS 800:2007]
        self.bearing_strength_concrete = self.cl_7_4_1_bearing_strength_concrete(self.footing_grade)  # N/mm^2 or MPa

        # slab base analyses (pinned connection)
        if self.connectivity == 'Welded Column Base':

            # minimum required area for the base plate [bearing stress = axial force / area of the base]
            self.min_area_req = self.load_axial_compression / self.bearing_strength_concrete  # mm^2

            # calculate projection by the 'Effective Area Method' [Reference: Clause 7.4.1.1, IS 800:2007]
            # the calculated projection is added by half times the hole dia on each side to avoid stress concentration near holes
            if self.dp_column_type == 'Rolled' or 'Welded':
                self.projection = self.calculate_c(self.column_bf, self.column_D, self.column_tw, self.column_tf, self.min_area_req,
                                                   self.anchor_hole_dia)  # mm
                self.projection = max(self.projection, self.end_distance)  # projection should at-least be equal to the end distance

            else:
                pass

            if self.projection <= 0:
                self.safe = False
                logger.error(": [Analysis Error] The value of the projection (c) as per the Effective Area Method is {} mm. [Reference:"
                             " Clause 7.4.1.1, IS 800: 2007]".format(self.projection))
                logger.warning(": [Analysis Error] The computed value of the projection is not suitable for performing the design.")
                logger.info(": [Analysis Error] Check the column section and its properties.")
                logger.info(": Re-design the connection")
            else:
                pass

            # updating the length and the width by incorporating the vaue of projection
            self.bp_length_provided = self.column_D + 2 * self.projection + 2 * self.end_distance  # mm
            self.bp_width_provided = self.column_bf + 2 * self.projection + 2 * self.edge_distance  # mm

            # check for the provided area against the minimum required area
            self.bp_area_provided = self.bp_length_provided * self.bp_width_provided  # mm^2

            # checking if the provided dimensions (length and width) are sufficient
            bp_dimensions = [self.bp_length_provided, self.bp_width_provided]

            n = 1
            while self.bp_area_provided < self.min_area_req:
                bp_update_dimensions = [bp_dimensions[-2], bp_dimensions[-1]]

                for i in bp_update_dimensions:
                    i += 25
                    bp_dimensions.append(i)
                    i += 1

                self.bp_area_provided = bp_dimensions[-2] * bp_dimensions[-1]  # mm^2, area according to the desired length and width
                n += 1

            self.bp_length_provided = bp_dimensions[-2]  # mm, updated length if while loop is True
            self.bp_width_provided = bp_dimensions[-1]  # mm, updated width if while loop is True
            self.bp_area_provided = self.bp_length_provided * self.bp_width_provided  # mm^2, update area if while loop is True

            # actual bearing pressure acting on the provided area of the base plate
            self.w = self.load_axial_compression / self.bp_area_provided  # N/mm^2 (MPa)

            # design of plate thickness
            # thickness of the base plate [Reference: Clause 7.4.3.1, IS 800:2007]
            self.plate_thk = self.projection * (math.sqrt((2.5 * self.w * self.gamma_m0) / self.dp_bp_fy))  # mm

            # number of anchor bolts provided outside the column flange
            self.anchor_nos_provided = 4

        elif self.connectivity == 'Moment Base Plate':

            # minimum design action effect on the column [Reference: clause 10.7, IS 800:2007]
            # the moment base plate shall be designed considering the bending moment acting on column as maximum of;
            # 1. external factored bending moment acting about the major axis of the column
            # 2. 50% of the moment capacity of the column

            z_pz = 1  # mm^3, TODO: call z_pz from db
            moment_capacity_column = (1 * z_pz * self.dp_column_fy) / self.gamma_m0
            moment_capacity_column = moment_capacity_column * 10 ** 6  # N-mm

            if self.load_moment_major < (0.50 * moment_capacity_column):
                self.load_moment_major = moment_capacity_column

                logger.warning("The external factored moment is less than the minimum recommended design action effect")
                logger.info("The minimum recommended design action effect (factored bending moment is {} kN-m)".format(moment_capacity_column))
                logger.info("The base plate is designed for a bending moment of {} kN-m".format(moment_capacity_column))
            else:
                pass

            # calculate eccentricity
            self.eccentricity_zz = self.load_moment_major / self.load_axial_compression  # mm, eccentricity about major (z-z) axis

            # Defining cases: Case 1: e <= L/6        (compression throughout the BP)
            #                 Case 2: L/6 < e < L/3   (compression throughout + moderate tension/uplift in the anchor bolts)
            #                 Case 3: e >= L/3        (compression + high tension/uplift in the anchor bolts)

            if self.eccentricity_zz <= self.bp_length_min / 6:  # Case 1

                self.moment_bp_case = 'Case1'

                # fixing length and width of the base plate
                width_min = 2 * self.load_axial_compression / (self.bp_length_min * self.bearing_strength_concrete)  # mm
                if width_min < self.bp_width_min:
                    width_min = self.bp_width_min
                else:
                    pass

                self.bp_length_provided = max(self.bp_length_min, width_min)  # mm, assigning maximum dimension to length
                self.bp_width_provided = min(self.bp_length_min, width_min)  # mm, assigning minimum dimension to width
                self.bp_area_provided = self.bp_length_provided * self.bp_width_provided  # mm^2

                # calculating the maximum and minimum bending stresses
                self.ze_zz = self.bp_width_provided * self.bp_length_provided ** 2 / 6  # mm^3, elastic section modulus of plate (BL^2/6)

                self.sigma_max_zz = (self.load_axial_compression / self.bp_area_provided) + (self.load_moment_major / self.ze_zz)  # N/mm^2
                self.sigma_min_zz = (self.load_axial_compression / self.bp_area_provided) - (self.load_moment_major / self.ze_zz)  # N/mm^2

                # calculating moment at the critical section

                # Assumption: the critical section (critical_xx) acts at a distance of 0.95 times the column depth, along the depth
                self.critical_xx = (self.bp_length_provided - 0.95 * self.column_D) / 2  # mm
                self.sigma_xx = (self.sigma_max_zz - self.sigma_min_zz) * (self.bp_length_provided - self.critical_xx) / self.bp_length_provided
                self.sigma_xx = self.sigma_xx + self.sigma_min_zz  # N/mm^2, bending stress at the critical section

                self.critical_M_xx = (self.sigma_xx * self.critical_xx ** 2 / 2) + \
                                     (0.5 * self.critical_xx * (self.sigma_max_zz - self.sigma_xx) * (2 / 3) * self.critical_xx)
                # N-mm, bending moment at critical section

                # equating critical moment with critical moment to compute the required minimum plate thickness
                # Assumption: The bending capacity of the plate is (M_d = 1.5*fy*Z_e/gamma_m0) [Reference: Clause 8.2.1.2, IS 800:2007]
                # Assumption: Z_e of the plate is = b*tp^2 / 6, where b = 1 for a cantilever strip of unit dimension

                self.plate_thk = math.sqrt((self.critical_M_xx * self.gamma_m0 * 6) / (1.5 * self.dp_bp_fy))  # mm

                self.tension_demand_anchor = 0  # there will be no tension acting on the anchor bolts in this case

            else:  # Case 2 and Case 3
                self.moment_bp_case = 'Case2&3'

                # fixing length and width of the base plate
                self.bp_length_provided = self.bp_length_min
                self.bp_width_provided = self.bp_width_min

                # calculating the distance (y) which lies under compression
                # Reference: Omer Blodgett, Column Bases, section 3.3, equation 13

                self.n = 2 * 10 ** 5 / (5000 * math.sqrt(self.cl_7_4_1_bearing_strength_concrete(self.footing_grade) / 0.45))
                self.anchor_area_tension = self.anchor_area[0] * (self.anchor_nos_provided / 2)  # mm^2, area of anchor under tension
                self.f = (self.bp_length_provided / 2) - self.end_distance  # mm

                k1 = 3 * (self.eccentricity_zz - self.bp_length_provided / 2)
                k2 = (6 * self.n * self.anchor_area_tension / self.bp_width_provided) * (self.f + self.eccentricity_zz)
                k3 = (self.bp_length_provided / 2 + self.f) * -k2

                # equation for finding 'y' is: y^3 + k1*y^2 + k2*y + k3 = 0
                roots = np.roots([1, k1, k2, k3])  # finding roots of the equation
                r_1 = roots[0]
                r_2 = roots[1]
                r_3 = roots[2]
                r = max(r_1, r_2, r_3)
                r = r.real  # separating the imaginary part

                self.y = round(r, 3)  # mm

                # finding maximum tension in the bolts for maximum permissible bearing stress (0.45*f_ck)
                self.tension_demand_anchor = ((self.bearing_strength_concrete * self.anchor_area_tension * self.n) / self.y) * \
                                             ((self.bp_length_provided / 2) + self.f - self.y)  # N
                self.tension_demand_anchor = round(self.tension_demand_anchor / 1000, 2)  # kN

                # computing the actual bending stress at the compression side
                # TODO: complete this check
                # self.flange_force_axial = self.dp_bp_fy * (self.column_bf * self.column_tf)  # N, load transferred by the flange
                # self.flange_force_moment = self.load_moment_major / (self.column_D - self.column_tf)  # N, tension acting at the flange
                # self.bp_area_compression = self.y * self.bp_width_provided  # mm^2, area of the base plate under compression

                # designing the plate thickness

                # 1. Yielding of the base plate due to bearing on concrete
                # finding the length of the critical section from the edge of the base plate on the compression side
                self.critical_xx = (self.bp_length_provided - 0.95 * self.column_D) / 2  # mm
                if self.y > self.critical_xx:
                    self.critical_xx = self.critical_xx
                else:
                    self.critical_xx = self.y

                # moment acting at the critical section due to applied loads
                # Assumption: The moment acting at the critical section is taken as 0.45*f_ck*B*critical_xx (plastic moment)
                self.critical_M_xx = (self.critical_xx * self.bearing_strength_concrete * self.bp_width_provided) * \
                                     (self.critical_xx / 2)  # N-mm

                # 2. Yielding of the base plate due to tension in the anchor bolts on the tension side
                lever_arm = (self.bp_length_provided / 2) - (self.column_D / 2) + (self.column_tf / 2) - self.end_distance  # mm

                # moment acting on the plate due to tension in the bolts
                moment_lever_arm = self.tension_demand_anchor * 1000 * lever_arm  # N-mm

                # updating the critical moment
                self.critical_M_xx = max(self.critical_M_xx, moment_lever_arm)  # N-mm

                # equating critical moment with critical moment to compute the required minimum plate thickness
                # Assumption: The bending capacity of the plate is (M_d = 1.5*fy*Z_e/gamma_m0) [Reference: Clause 8.2.1.2, IS 800:2007]
                # Assumption: Z_e of the plate is = b*tp^2 / 6, where b = 1 for a cantilever strip of unit dimension

                self.plate_thk = math.sqrt((self.critical_M_xx * self.gamma_m0 * 6) / (1.5 * self.dp_bp_fy * self.bp_width_provided))  # mm

            # design of the anchor bolt(s) required to resist tension due to bending moment only
            self.tension_capacity_anchor = self.cl_10_3_5_bearing_bolt_tension_resistance(self.anchor_fu_fy[0], self.anchor_fu_fy[1],
                                                                                          self.anchor_area[0], self.anchor_area[1],
                                                                                          safety_factor_parameter=self.dp_weld_fab)  # N
            self.tension_capacity_anchor = round(self.tension_capacity_anchor / 1000, 2)  # kN

            # design number of anchor bolts required to resist tension
            # Assumption: The minimum number of anchor bolts is 2, for stability purpose.
            self.tension_bolts_req = max(self.tension_demand_anchor / self.tension_capacity_anchor, 2)

            # if the number of bolts required to resist tension exceeds 2 in number, then the loop will check
            # for a higher diameter of bolt from the given list of anchor diameters by the user.
            n = 1
            while self.tension_bolts_req > 3:  # the maximum number of bolts that can be accommodated is 3
                bolt_list = self.anchor_dia[n - 1:]

                for i in bolt_list:
                    self.anchor_dia_provided = i
                    break

                self.anchor_area = self.bolt_area(self.table1(self.anchor_dia_provided)[0])
                self.tension_capacity_anchor = self.cl_10_3_5_bearing_bolt_tension_resistance(self.anchor_fu_fy[0], self.anchor_fu_fy[1],
                                                                                              self.anchor_area[0], self.anchor_area[1],
                                                                                              safety_factor_parameter=self.dp_weld_fab)  # N
                self.tension_capacity_anchor = round(self.tension_capacity_anchor / 1000, 2)  # kN

                self.tension_bolts_req = max(self.tension_demand_anchor / self.tension_capacity_anchor, 2)
                n += 1

                self.anchor_dia_provided = self.table1(i)[0]  # updating the initialised anchor diameter

                if n > len(self.anchor_dia):
                    self.safe = False
                    # TODO: give log errors
                    logger.error("Cannot compute anchor bolt for resisting the uplift force")

            if self.moment_bp_case == 'Case1':
                self.anchor_nos_provided = self.anchor_nos_provided
            else:
                self.anchor_nos_provided = 2 * self.tension_bolts_req

        elif self.connectivity == "Welded+Bolted Column Base":
            pass

        elif self.connectivity == "Hollow/Tubular Column Base":
            pass

        # assign appropriate plate thickness

        self.plate_thk = max(self.plate_thk, self.column_tf)  # base plate thickness should be larger than the flange thickness

        # assigning plate thickness according to the available standard sizes
        # the thicknesses of the flats (in mm) listed below is obtained from SAIL's product brochure
        standard_plate_thk = [8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 36, 40, 45, 50, 56, 63, 75, 80, 90, 100, 110, 120]

        sort_plate = filter(lambda x: self.plate_thk <= x <= 120, standard_plate_thk)

        for i in sort_plate:
            self.plate_thk = i  # plate thickness provided (mm)
            break

    def anchor_bolt_design(self):
        """ Perform design checks for the anchor bolt

        Args:

        Returns:
        """
        # updating the anchor area (provided outside flange), if the diameter is updated in tension check
        self.anchor_area = self.bolt_area(self.anchor_dia_provided)  # list of areas [shank area, thread area] mm^2
        self.anchor_grade_tension = self.anchor_grade

        if self.connectivity == 'Moment Base Plate':

            # design of anchor bolts to resist axial tension/uplift force
            if self.load_axial_tension > 0:
                self.anchor_inside_flange = 'Yes'

                self.anchor_dia_uplift = self.anchor_dia_provided  # initialise the diameter required equal to the anchor dia provided outside flange
                self.tension_capacity_anchor_uplift = self.tension_capacity_anchor

                self.anchor_nos_uplift = self.load_axial_tension / (self.tension_capacity_anchor_uplift * 1000)  # number of bolts req to resist uplift
                self.anchor_nos_uplift = round_up(self.anchor_nos_uplift, 2)

                # if the number of bolts required to resist uplift exceeds 2 in number, then the loop will check
                # for a higher diameter of bolt from the given list of anchor diameters by the user.
                n = 1
                while self.anchor_nos_uplift > 2:  # the maximum number of bolts that can be accommodated is 3
                    bolt_list = self.anchor_dia[n - 1:]

                    for i in bolt_list:
                        self.anchor_dia_uplift = i
                        break

                    self.anchor_area = self.bolt_area(self.table1(self.anchor_dia_uplift)[0])
                    self.tension_capacity_anchor_uplift = self.cl_10_3_5_bearing_bolt_tension_resistance(self.anchor_fu_fy[0], self.anchor_fu_fy[1],
                                                                                                         self.anchor_area[0], self.anchor_area[1],
                                                                                                         safety_factor_parameter=self.dp_weld_fab)  # N
                    self.tension_capacity_anchor_uplift = round(self.tension_capacity_anchor_uplift / 1000, 2)  # kN

                    self.anchor_nos_uplift = max(self.load_axial_tension / self.tension_capacity_anchor_uplift, 2)
                    n += 1

                    self.anchor_dia_uplift = self.table1(i)[0]  # updating the initialised anchor diameter for uplift force

                    if n > len(self.anchor_dia):
                        self.safe = False
                        # TODO: give log errors
                        logger.error("Cannot compute anchor bolt for resisting the uplift force")

                # updating total number of anchor bolts required (bolts outside flange for resisting moment + inside flange for resisting uplift)
                self.anchor_nos_provided = self.anchor_nos_provided + self.anchor_nos_uplift

            else:
                self.anchor_inside_flange = 'No'
                self.anchor_nos_uplift = 0
                self.anchor_dia_uplift = self.anchor_dia_provided
                self.tension_capacity_anchor_uplift = self.tension_capacity_anchor
                self.anchor_nos_uplift = 0

        else:
            pass

        # design strength of the anchor bolt for shear [Reference: Clause 10.3.2, IS 800:2007; Section 3, IS 5624:1993]
        # Assumption: number of shear planes passing through - the thread is 1 (n_n) and through the shank is 0 (n_s)

        self.shear_capacity_anchor = self.cl_10_3_3_bolt_shear_capacity(self.dp_anchor_fu_overwrite, self.anchor_area[1],
                                                                        self.anchor_area[0], 1, 0, self.dp_weld_fab)
        self.shear_capacity_anchor = round(self.shear_capacity_anchor / 1000, 2)  # kN

        self.bearing_capacity_anchor = self.cl_10_3_4_bolt_bearing_capacity(self.dp_bp_fu, self.dp_anchor_fu_overwrite, self.plate_thk,
                                                                            self.anchor_dia_provided, self.end_distance,
                                                                            self.pitch_distance, self.dp_anchor_hole, self.dp_weld_fab)
        self.bearing_capacity_anchor = round(self.bearing_capacity_anchor / 1000, 2)  # kN

        self.anchor_capacity = min(self.shear_capacity_anchor, self.bearing_capacity_anchor)  # kN

        # information message to the user
        if self.load_shear_major > 0:
            # TODO
            logger.info(": [Anchor Bolt] The anchor bolt is not designed to resist any shear force")
        else:
            pass

        # Design for shear acting along any axis

        if self.load_shear_major or self.load_shear_minor > 0:
            # The shear transfer follows the following load transfer mechanism:

            # Check 1: The shear is transferred through the anchor bolts. The bolts on the tension side are critical and
            # are checked for combined shear + tension
            # Check 2: The shear is then resisted by the friction between the base plate and the grout material
            # Check 3: If the shear is still high, then a shear key is provided. The shear key resists shear by bearing
            # on the concrete surface

            if self.connectivity == 'Moment Base Plate':

                if self.moment_bp_case == 'Case1':
                    self.combined_capacity_anchor = 'N/A'

                else:
                    # Check 1: Combined shear + Tension [Reference: cl.10.3.6, IS 800:2007]
                    # v_sb is calculated considering shear distribution in bolts only on the tension side (outside flange), this is the critical case
                    self.v_sb = (max(self.load_shear_major, self.load_shear_minor) * 10 ** -3) / (self.anchor_nos_provided / 2)  # kN
                    self.v_db = self.anchor_capacity  # kN
                    self.t_b = self.tension_demand_anchor / self.tension_bolts_req  # kN
                    self.t_db = self.tension_capacity_anchor  # kN
                    self.combined_capacity_anchor = self.cl_10_3_6_bearing_bolt_combined_shear_and_tension(self.v_sb, self.v_db, self.t_b, self.t_db)
                    self.combined_capacity_anchor = round(self.combined_capacity_anchor, 3)

                    if self.combined_capacity_anchor > 1.0:
                        logger.error(": [Large Shear Force] The shear force acting on the base plate is large.")
                        logger.info(": [Large Shear Force] Provide shear key to safely transfer the shear force.")
                        logger.error(": [Anchor Bolt] The anchor bolt fails due to combined shear + tension [Reference: Clause 10.3.6, "
                                     "IS 800:2007].")

                        # re-design anchor bolts if it fails in combined shear + tension check
                        # Algorithm:
                        # Step 1: Try with higher diameter bolt,
                        # Step 2: If the check still fails, try with more number of bolts

                        # Step 1
                        n = 1
                        while self.combined_capacity_anchor > 1.0:
                            bolt_list = self.anchor_dia[n - 1:]

                            for i in bolt_list:
                                self.anchor_dia_provided = self.table1(i)[0]
                                break

                            # re-calculating the capacities with updated diameter
                            self.anchor_area = self.bolt_area(self.anchor_dia_provided)

                            self.shear_capacity_anchor = self.cl_10_3_3_bolt_shear_capacity(self.dp_anchor_fu_overwrite, self.anchor_area[1],
                                                                                            self.anchor_area[0], 1, 0, self.dp_weld_fab)
                            self.shear_capacity_anchor = round(self.shear_capacity_anchor / 1000, 2)  # kN

                            self.bearing_capacity_anchor = self.cl_10_3_4_bolt_bearing_capacity(self.dp_bp_fu, self.dp_anchor_fu_overwrite,
                                                                                                self.plate_thk,
                                                                                                self.anchor_dia_provided, self.end_distance,
                                                                                                self.pitch_distance, self.dp_anchor_hole,
                                                                                                self.dp_weld_fab)
                            self.bearing_capacity_anchor = round(self.bearing_capacity_anchor / 1000, 2)  # kN

                            self.anchor_capacity = min(self.shear_capacity_anchor, self.bearing_capacity_anchor)  # kN

                            self.tension_capacity_anchor = self.cl_10_3_5_bearing_bolt_tension_resistance(self.anchor_fu_fy[0], self.anchor_fu_fy[1],
                                                                                                          self.anchor_area[0], self.anchor_area[1],
                                                                                                          safety_factor_parameter=self.dp_weld_fab)  # N
                            self.tension_capacity_anchor = round(self.tension_capacity_anchor / 1000, 2)  # kN

                            self.v_sb = (max(self.load_shear_major, self.load_shear_minor) * 10 ** -3) / (self.anchor_nos_provided / 2)  # kN
                            self.v_db = self.anchor_capacity  # kN
                            self.t_b = self.tension_demand_anchor / self.tension_bolts_req  # kN
                            self.t_db = self.tension_capacity_anchor  # kN
                            self.combined_capacity_anchor = self.cl_10_3_6_bearing_bolt_combined_shear_and_tension(self.v_sb, self.v_db, self.t_b,
                                                                                                                   self.t_db)
                            self.combined_capacity_anchor = round(self.combined_capacity_anchor, 3)
                            n += 1

                            # updating the initialised anchor diameter which passes the combined shear + tension check
                            self.anchor_dia_provided = self.anchor_dia_provided

                            # Step 2
                            if n > len(self.anchor_dia):
                                if self.tension_bolts_req <= 2:
                                    self.tension_bolts_req += 1
                                    self.anchor_nos_provided = 2 * self.tension_bolts_req

                                    # check with increased number of bolts
                                    n = 1
                                    while self.combined_capacity_anchor > 1.0:
                                        bolt_list = self.anchor_dia[n - 1:]

                                        for i in bolt_list:
                                            self.anchor_dia_provided = self.table1(i)[0]
                                            break

                                        # re-calculating the capacities with updated diameter and increased number of bolts
                                        self.anchor_area = self.anchor_area = self.bolt_area(self.anchor_dia_provided)

                                        self.shear_capacity_anchor = self.cl_10_3_3_bolt_shear_capacity(self.dp_anchor_fu_overwrite,
                                                                                                        self.anchor_area[1],
                                                                                                        self.anchor_area[0], 1, 0,
                                                                                                        self.dp_weld_fab)
                                        self.shear_capacity_anchor = round(self.shear_capacity_anchor / 1000, 2)  # kN

                                        self.bearing_capacity_anchor = self.cl_10_3_4_bolt_bearing_capacity(self.dp_bp_fu,
                                                                                                            self.dp_anchor_fu_overwrite,
                                                                                                            self.plate_thk,
                                                                                                            self.anchor_dia_provided,
                                                                                                            self.end_distance,
                                                                                                            self.pitch_distance,
                                                                                                            self.dp_anchor_hole,
                                                                                                            self.dp_weld_fab)
                                        self.bearing_capacity_anchor = round(self.bearing_capacity_anchor / 1000, 2)  # kN

                                        self.anchor_capacity = min(self.shear_capacity_anchor, self.bearing_capacity_anchor)  # kN

                                        self.tension_capacity_anchor = self.cl_10_3_5_bearing_bolt_tension_resistance(self.anchor_fu_fy[0],
                                                                                                                      self.anchor_fu_fy[1],
                                                                                                                      self.anchor_area[0],
                                                                                                                      self.anchor_area[1],
                                                                                                                      safety_factor_parameter=self.dp_weld_fab)  # N
                                        self.tension_capacity_anchor = round(self.tension_capacity_anchor / 1000, 2)  # kN

                                        self.v_sb = (max(self.load_shear_major, self.load_shear_minor) * 10 ** -3) / (
                                                    self.anchor_nos_provided / 2)  # kN
                                        self.v_db = self.anchor_capacity  # kN
                                        self.t_b = self.tension_demand_anchor / self.tension_bolts_req  # kN
                                        self.t_db = self.tension_capacity_anchor  # kN
                                        self.combined_capacity_anchor = self.cl_10_3_6_bearing_bolt_combined_shear_and_tension(self.v_sb, self.v_db,
                                                                                                                               self.t_b,
                                                                                                                               self.t_db)
                                        self.combined_capacity_anchor = round(self.combined_capacity_anchor, 3)
                                        n += 1

                                        self.anchor_dia_provided = i  # updating the initialised anchor diameter which passes the combined shear + tension check

                                        if n > len(self.anchor_dia):
                                            # TODO: give log errors
                                            logger.error("Cannot compute")
                                            logger.error("Cannot compute anchor bolt for resisting the uplift force")
                    else:
                        pass

            else:
                # Check 2: Friction between base plate and the grout material [Reference: AISC Design Guide, section 3.5]
                # The coefficient of friction between steel and the grout is 0.55, whereas between steel and concrete is 0.7
                self.shear_resistance = 0.55 * self.load_axial_compression  # N
                self.shear_resistance = min(self.shear_resistance, 0.2 * (self.bearing_strength_concrete / 0.45) * self.bp_area_provided)  # N

                if self.shear_resistance < max(self.load_shear_major, self.load_shear_minor):
                    self.shear_key_required = 'Yes'

                    # Check 3: Provide shear key
                    # Note: The shear key thickness shall be at-least equal to the base plate thickness to avoid bending
                    self.shear_key_thk = self.plate_thk  # mm

                    if self.load_shear_major > 0:
                        self.shear_key_along_ColDepth= 'Yes'
                        self.shear_key_len_ColDepth = self.column_D  # mm
                        self.shear_key_depth_ColDepth = self.load_shear_major / ((self.bearing_strength_concrete / 0.45) *
                                                                                 self.shear_key_len_ColDepth)  # mm
                        self.shear_key_depth_ColDepth = max(self.shear_key_depth_ColDepth, self.grout_thk + 150)  # mm
                    else:
                        self.shear_key_along_ColWidth = 'Yes'
                        self.shear_key_len_ColWidth = self.column_bf  # mm
                        self.shear_key_depth_ColWidth = self.load_shear_minor / ((self.bearing_strength_concrete / 0.45) *
                                                                                 self.shear_key_len_ColWidth)  # mm
                        self.shear_key_depth_ColWidth = max(self.shear_key_depth_ColWidth, self.grout_thk + 150)  # mm

                else:
                    self.shear_key_required = 'No'

                # Check 1: Not applicable
                self.combined_capacity_anchor = 'N/A'
        else:
            # TODO
            self.combined_capacity_anchor = 'N/A'
            logger.info("There is no shear force acting on the anchor bolts")
            logger.info("No combined shear-tension check is required")

        # if self.safe:
        #     pass
        # else:
        #     logger.error(": [Anchor Bolt] Unexpected failure occurred.")
        #     logger.error(": [Anchor Bolt] Cannot compute capacity checks for the anchor bolt.")
        #     logger.info(": [Anchor Bolt] Check the input values and re-design the connection.")

        # validation of anchor bolt length [Reference: IS 5624:1993, Table 1]
        self.anchor_length_min = self.table1(self.anchor_bolt)[1]
        self.anchor_length_max = self.table1(self.anchor_bolt)[2]

        # design of anchor length [Reference: Design of Steel Structures by N. Subramanian 2nd. edition 2018, Example 15.5]
        if self.connectivity == 'Welded Column Base':
            self.anchor_length_provided = self.anchor_length_min  # mm

        # Equation: T_b = k * sqrt(fck) * (anchor_length_req)^1.5
        elif self.connectivity == 'Moment Base Plate':

            if self.moment_bp_case == 'Case1':
                self.anchor_length_provided = self.anchor_length_min  # mm

            else:
                # length of anchor for cast-in situ anchor bolts (k = 15.5)
                self.anchor_length_provided = (self.tension_capacity_anchor * 1000 /
                                               (15.5 * math.sqrt(self.bearing_strength_concrete / 0.45))) ** (1 / 1.5)  # mm
                self.anchor_length_provided = max(self.anchor_length_provided, self.anchor_length_min)

            logger.info(": [Anchor Bolt Length] The length of the anchor bolt is computed assuming the anchor bolt is casted in-situ"
                        " during the erection of the column.")

        elif self.connectivity == 'Welded+Bolted Column Base':
            pass
        elif self.connectivity == 'Hollow/Tubular Column Base':
            pass

        # updating anchor length (adding the length above the concrete pedestal)
        self.grout_thk = 50  # mm
        if self.connectivity == 'Moment Base Plate':
            self.plate_washer_thk = self.square_washer_dimensions(max(self.anchor_dia_provided, self.anchor_dia_uplift))['washer_thk']  # washer thickness, mm
            self.nut_thk = self.nutThick_Calculation(max(self.anchor_dia_provided, self.anchor_dia_uplift))  # nut thickness, mm
        elif self.connectivity == 'Welded Column Base':
            self.plate_washer_thk = self.square_washer_dimensions(self.anchor_dia_provided)['washer_thk']  # washer thickness, mm
            self.nut_thk = self.nutThick_Calculation(self.anchor_dia_provided)  # nut thickness, mm

        self.anchor_len_below_footing = self.anchor_length_provided  # mm
        self.anchor_len_above_footing = self.grout_thk + self.plate_thk + self.plate_washer_thk + self.nut_thk + 20  # mm, 20 mm is extra len

        self.anchor_length_provided = self.anchor_len_below_footing + self.anchor_len_above_footing  # total length of the anchor bolt

        # calling value of the anchor length from user from design preferences
        if self.dp_anchor_length == 0:
            self.anchor_length_provided = self.anchor_length_provided  # mm
        else:
            self.anchor_length_provided = self.dp_anchor_length

        if self.anchor_length_provided < self.anchor_length_min or self.anchor_length_provided > self.anchor_length_max:
            self.safe = False
            logger.error(": [Anchor Bolt] The length of the anchor bolt provided occurred out of the preferred range.")

        else:
            logger.info(": [Anchor Bolt] The preferred range of length for the anchor bolt of thread size {} is as follows:"
                        .format(self.anchor_dia_provided))
            logger.info(": [Anchor Bolt] Minimum length = {} mm, Maximum length = {} mm."
                        .format(self.anchor_length_min, self.anchor_length_max))
            logger.info(": [Anchor Bolt] The provided length of the anchor bolt is {} mm".format(self.anchor_length_provided))
            logger.info(": [Anchor Bolt] Designer/Erector should provide adequate anchorage depending on the availability "
                        "of standard lengths and sizes, satisfying the suggested range.")
            logger.info(": [Anchor Bolt] Reference: IS 5624:1993, Table 1.")

    def design_weld(self):
        """ design weld for the base plate and stiffeners

        Args:

        Returns:
        """
        # design the weld connecting the column and the stiffeners to the base plate

        self.weld_fu = min(self.dp_weld_fu_overwrite, self.dp_column_fu)

        # length of the stiffener plate available in case of stiffener requirement/or extra welding
        self.stiffener_plt_len_along_flange = (self.bp_width_provided - self.column_bf) / 2  # mm (each, along the flange)
        self.stiffener_plt_len_along_web = (self.bp_length_provided - self.column_D) / 2  # mm (each, along the web)
        self.stiffener_plt_len_across_web = max(self.stiffener_plt_len_along_flange, self.stiffener_plt_len_along_web)  # mm (each, across the web)

        # design of fillet weld
        if self.weld_type == 'Fillet Weld':

            if self.connectivity == 'Welded Column Base':

                if self.dp_column_type == 'Rolled' or 'Welded':

                    # defining the maximum limit of weld size that can be provided, which is equal to/less than the flange/web thickness
                    self.weld_size_flange_max = round_down(self.column_tf, 2)  # mm
                    self.weld_size_web_max = round_down(self.column_tw, 2)  # mm

                    # available length for welding along the flange and web of the column, without the stiffeners
                    length_available_flange = 2 * (self.column_bf + (self.column_bf - self.column_tw - (2 * self.column_r1)))  # mm
                    length_available_web = 2 * (self.column_D - (2 * self.column_tf) - (2 * self.column_r1))  # mm

                    # TODO: check end returns reduction
                    # Note: The effective length of weld is calculated by assuming 1% reduction in length at each end return. Since, the
                    # total number of end returns are 12, a total of 12% reduction (8% at flange and 4% at web) is incorporated into the
                    # respective 'effective' lengths.
                    self.effective_length_flange = length_available_flange - (0.08 * length_available_flange)  # mm
                    self.effective_length_web = length_available_web - (0.04 * length_available_web)  # mm

                    self.strength_unit_len = self.load_axial_compression / (self.effective_length_flange + self.effective_length_web)  # N/mm
                    self.weld_size = self.calc_weld_size_from_strength_per_unit_len(self.strength_unit_len,
                                                                                    [self.dp_weld_fu_overwrite, self.dp_column_fu],
                                                                                    [self.plate_thk, self.column_tf], self.dp_weld_fab)  # mm

                    self.weld_size_flange = self.weld_size  # mm
                    self.weld_size_web = self.weld_size  # mm

                    # check against maximum allowed weld size at web
                    # checking if stiffener plates are required for providing extra length of weld
                    if self.weld_size_web > self.weld_size_web_max:
                        # Case 1: Adding stiffeners along the flanges of the column on either sides (total four in number)
                        self.stiffener_along_flange = 'Yes'

                        # length available on each stiffener plate for (fillet) welding on either sides
                        # effective length assuming 2% reduction to incorporate end returns
                        self.eff_stiffener_plt_len_along_flange = (self.stiffener_plt_len_along_flange * 2) - \
                                                                  (0.02 * self.stiffener_plt_len_along_flange)  # mm (for each stiffener)
                        # total effective len available including four stiffeners
                        self.total_eff_len_available = self.effective_length_flange + self.effective_length_web + \
                                                       (4 * self.eff_stiffener_plt_len_along_flange)  # mm

                        # relative strength of weld per unit weld length and weld size including stiffeners along the flange
                        self.strength_unit_len = self.load_axial_compression / self.total_eff_len_available  # N/mm
                        self.weld_size = self.calc_weld_size_from_strength_per_unit_len(self.strength_unit_len,
                                                                                               [self.dp_weld_fu_overwrite, self.dp_column_fu],
                                                                                               [self.plate_thk, self.column_tf], self.dp_weld_fab)  # mm

                        self.weld_size_web = self.weld_size  # mm

                    # Second iteration: checking the maximum weld size (at web)
                    if self.weld_size_web > self.weld_size_web_max:
                        # Case 2: Adding stiffeners along web of the column (total two in number)
                        self.stiffener_along_web = 'Yes'

                        self.eff_stiffener_plt_len_along_web = (self.stiffener_plt_len_along_web * 2) - (0.02 * self.stiffener_plt_len_along_web)  # mm

                        # TODO: deduce notch size
                        # total effective len available including four stiffeners along flange and two along the web
                        self.total_eff_len_available = self.total_eff_len_available + (2 * self.eff_stiffener_plt_len_along_web)  # mm

                        # relative strength of weld per unit weld length and weld size, including stiffeners along the flange and the web
                        self.strength_unit_len = self.load_axial_compression / self.total_eff_len_available  # N/mm
                        self.weld_size = self.calc_weld_size_from_strength_per_unit_len(self.strength_unit_len,
                                                                                               [self.dp_weld_fu_overwrite, self.dp_column_fu],
                                                                                               [self.plate_thk, self.column_tf], self.dp_weld_fab)  # mm

                        self.weld_size_web = self.weld_size  # mm

                        # Third iteration: checking the maximum weld size (at web)
                        if self.weld_size_web > self.weld_size_web_max:
                            # Case 3: Adding stiffeners across the web of the column, between the column depth (total two in number)
                            self.stiffener_across_web = 'Yes'

                            len_required = (self.load_axial_compression * math.sqrt(3) * self.gamma_mw) / (0.7 * self.weld_size_web_max * self.weld_fu)  # mm
                            # Adding 16% of the total length to incorporate end returns (total 16 end returns in this case)
                            len_required = len_required + (0.16 * len_required)  # mm

                            len_stiffener_req_across_web = len_required - self.total_eff_len_available  # mm
                            len_stiffener_available_across_web = 4 * ((self.bp_width_provided / 2) - (self.column_tw / 2) - self.edge_distance)  # mm

                            if len_stiffener_req_across_web < len_stiffener_available_across_web:

                                self.stiffener_plt_len_across_web = max(self.stiffener_plt_len_across_web, len_stiffener_req_across_web)  # mm
                                self.total_eff_len_available = self.total_eff_len_available + (4 * self.stiffener_plt_len_across_web)  # mm

                                # relative strength of weld per unit weld length,
                                # and, weld size, including stiffeners along the flange, web and across the web
                                self.strength_unit_len = self.load_axial_compression / self.total_eff_len_available  # N/mm
                                self.weld_size = self.calc_weld_size_from_strength_per_unit_len(self.strength_unit_len,
                                                                                                [self.dp_weld_fu_overwrite, self.dp_column_fu],
                                                                                                [self.plate_thk, self.column_tf],
                                                                                                self.dp_weld_fab)  # mm

                                self.weld_size_web = self.weld_size  # mm

                                if self.weld_size_web > self.weld_size_web_max:
                                    self.weld_size_web = self.weld_size_web_max
                            else:
                                self.design_status = False
                                # TODO: add log messages

                            # TODO: add log messages
                        else:
                            pass

                    else:
                        self.stiffener_along_flange = 'No'
                        self.stiffener_along_web = 'No'
                        self.stiffener_across_web = 'No'

                        self.weld_size_flange = self.weld_size  # mm
                        self.weld_size_stiffener = self.weld_size  # mm

                else:  # TODO: add checks for other type(s) of column section here (Example: built-up, star shaped etc.)
                    pass

            elif self.connectivity == 'Hollow/Tubular Column Base':  # TODO: add calculations for hollow sections
                pass

        # design of butt/groove weld
        else:
            if self.connectivity == 'Welded Column Base':
                self.stiffener_along_flange = 'No'
                self.stiffener_along_web = 'No'

            elif self.connectivity == 'Moment Base Plate':
                self.stiffener_along_flange = 'Yes'
                self.stiffener_along_web = 'Yes'
                self.stiffener_across_web = 'No'

            self.weld_size_flange = self.column_tf  # mm
            self.weld_size_web = self.column_tw  # mm

    def design_stiffeners(self):
        """ design and detail the stiffener plates

        Args:

        Returns:
        """
        # define material parameters
        self.stiffener_fy = self.dp_column_fy  # MPa
        self.epsilon = math.sqrt(250 / self.stiffener_fy)

        # check for the limiting width to the thickness ratio of the column web [Reference: Cl. 3.7.2 and 3.7.4, Table 2, IS 800:2007]
        # if the web does not classify as 'Plastic' section, stiffener shall be provided across the web to limit the effective width
        ratio = (self.column_D - (2 * self.column_tf)) / self.column_tw  # d/t_w

        # Check 1: Axial compression
        if self.connectivity == 'Welded Column Base':
            if ratio > (42 * self.epsilon):
                self.stiffener_across_web = 'Yes'
            else:
                self.stiffener_across_web = 'No'

        # Check 2: Neutral axis at mid depth of the column
        elif self.connectivity == 'Moment Base Plate':
            if ratio > (84 * self.epsilon):
                self.stiffener_across_web = 'Yes'
            else:
                self.stiffener_across_web = 'No'

        # Check 3: Generally (when there is axial tension/uplift force acting on the column)
        if self.load_axial_tension > 0:
            actual_stress = self.load_axial_tension / ((self.column_D - (2 * self.column_tf)) * self.column_tw)
            r_1 = - (actual_stress / self.dp_column_fy)  # r_1 is negative for axial tension

            if ratio > (((84 * self.epsilon) / (1 + r_1)) or (42 * self.epsilon)):
                self.stiffener_across_web = 'Yes'
            else:
                self.stiffener_across_web = 'No'

        # design of stiffener
        if self.connectivity == 'Welded Column Base' or 'Moment Base Plate':
            self.stiffener_across_web = 'Yes'
            if (self.stiffener_along_flange or self.stiffener_along_web or self.stiffener_across_web) == 'Yes':

                # thickness of the stiffener plate as per Table 2 of IS 800:2007 [b/t_f <= 13.6 * epsilon]
                thk_req_stiffener_along_flange = self.stiffener_plt_len_along_flange / (13.6 * self.epsilon)  # mm
                thk_req_stiffener_along_web = self.stiffener_plt_len_along_web / (13.6 * self.epsilon)  # mm
                thk_req_stiffener_across_web = self.stiffener_plt_len_across_web / (13.6 * self.epsilon)  # mm

                # stiffener plate should be at-least equal to the flange thickness along the flange and web thickness along the web
                self.stiffener_plt_thick_along_flange = round_up(thk_req_stiffener_along_flange, 2, self.column_tf)  # mm
                self.stiffener_plt_thick_along_web = round_up(thk_req_stiffener_along_web, 2, self.column_tw)  # mm
                self.stiffener_plt_thick_across_web = round_up(thk_req_stiffener_across_web, 2, self.column_tw)  # mm

                # height of the stiffener plate
                # the size of the landing is 100 mm along its vertical side and 50 mm along its horizontal side
                # the assumed inclination of the stiffener plate is 45 degrees
                self.stiffener_plt_height_along_flange = self.stiffener_plt_len_along_flange + 50  # mm
                self.stiffener_plt_height_along_web = self.stiffener_plt_len_along_web + 50  # mm
                self.stiffener_plt_height_across_web = self.stiffener_plt_len_across_web + 50  # mm

                # defining stresses for the connectivity types
                # sigma_max_zz - at the edge of the base plate on compression side
                # sigma_xx - at the critical section (0.95 * column depth) of the base plate on compression side
                # sigma_web - at the centre of the base plate on compression side
                if self.connectivity == 'Welded Column Base':
                    self.sigma_max_zz = self.w  # MPa
                    self.sigma_xx = self.w  # MPa
                    self.sigma_web = self.w  # MPa
                else:
                    if self.moment_bp_case == 'Case1':
                        self.sigma_max_zz = self.sigma_max_zz
                        self.sigma_xx = self.sigma_xx
                        self.sigma_web = 0.50 * self.sigma_max_zz
                    else:
                        self.sigma_max_zz = 0.45 * self.bearing_strength_concrete
                        self.sigma_xx = 0.45 * self.bearing_strength_concrete
                        if self.y < (self.bp_length_provided / 2):
                            self.sigma_web = 0.0
                        else:
                            self.sigma_web = self.sigma_xx

                # shear yielding and moment capacity checks for the stiffener - along the flange
                if self.stiffener_along_flange == 'Yes':
                    # shear and moment demand calculations
                    self.shear_on_stiffener_along_flange = self.sigma_xx * self.stiffener_plt_len_along_flange * self.stiffener_plt_height_along_flange
                    self.shear_on_stiffener_along_flange = round((self.shear_on_stiffener_along_flange / 1000), 3)  # kN

                    self.moment_on_stiffener_along_flange = self.sigma_xx * self.stiffener_plt_height_along_flange * \
                                                            self.stiffener_plt_len_along_flange ** 2 * 0.5
                    self.moment_on_stiffener_along_flange = round((self.moment_on_stiffener_along_flange * 10 ** -6), 3)  # kN-m

                    # shear and moment capacity calculations
                    self.shear_capa_stiffener_along_flange = IS800_2007.cl_8_4_design_shear_strength((self.stiffener_plt_height_along_flange *
                                                                                                self.stiffener_plt_thick_along_flange), self.stiffener_fy)
                    self.shear_capa_stiffener_along_flange = round((self.shear_capa_stiffener_along_flange / 1000), 3)  # kN

                    self.z_e_stiffener_along_flange = (self.stiffener_plt_thick_along_flange * self.stiffener_plt_height_along_flange ** 2) / 6  # mm^3

                    self.moment_capa_stiffener_along_flange = IS800_2007.cl_8_2_1_2_design_moment_strength(self.z_e_stiffener_along_flange, 0,
                                                                                                        self.stiffener_fy, section_class='semi-compact')
                    self.moment_capa_stiffener_along_flange = round((self.moment_capa_stiffener_along_flange * 10 ** -6), 3)  # kN-m

                    # checks
                    if self.shear_on_stiffener_along_flange > (0.6 * self.shear_capa_stiffener_along_flange):
                        logger.warning("Fails in shear")
                        logger.info("Improvising thk")
                        self.stiffener_plt_thick_along_flange = (math.sqrt(3) * self.gamma_m0 * self.shear_on_stiffener_along_flange * 1000) / \
                                                                (self.stiffener_fy * self.stiffener_plt_height_along_flange)
                        self.stiffener_plt_thick_along_flange = round_up(self.stiffener_plt_thick_along_flange, 2)  # mm

                        # re-calculating the moment capacity by incorporating the improvised stiffener thickness along flange
                        self.z_e_stiffener_along_flange = (self.stiffener_plt_thick_along_flange * self.stiffener_plt_height_along_flange ** 2) / 6  # mm^3

                        self.moment_capa_stiffener_along_flange = IS800_2007.cl_8_2_1_2_design_moment_strength(self.z_e_stiffener_along_flange, 0,
                                                                                                               self.stiffener_fy,
                                                                                                               section_class='semi-compact')
                        self.moment_capa_stiffener_along_flange = round((self.moment_capa_stiffener_along_flange * 10 ** -6), 3)  # kN-m
                    else:
                        pass

                    if self.moment_on_stiffener_along_flange > self.moment_capa_stiffener_along_flange:
                        logger.warning("Fails in moment")
                        logger.info("Improvising thk")
                        self.stiffener_plt_thick_along_flange = (6 * self.gamma_m0 * self.moment_on_stiffener_along_flange * 10 ** 6) / \
                                                             (self.stiffener_fy * self.stiffener_plt_height_along_flange ** 2)
                        self.stiffener_plt_thick_along_flange = round_up(self.stiffener_plt_thick_along_flange, 2)  # mm
                    else:
                        pass
                else:
                    pass

                # shear yielding and moment capacity checks for the stiffener - along the web
                if self.stiffener_along_web == 'Yes':
                    # shear and moment demand calculations
                    self.shear_on_stiffener_along_web = ((self.sigma_max_zz + self.sigma_xx) / 2) * self.stiffener_plt_len_along_web * \
                                                        self.stiffener_plt_height_along_web
                    self.shear_on_stiffener_along_web = round((self.shear_on_stiffener_along_web / 1000), 3)  # kN

                    self.moment_on_stiffener_along_web = (self.sigma_xx * self.stiffener_plt_height_along_web * self.stiffener_plt_len_along_web ** 2 * 0.5) \
                                                         + (0.5 * self.stiffener_plt_len_along_web * (self.sigma_max_zz - self.sigma_xx) *
                                                            self.stiffener_plt_height_along_web * (2 / 3) * self.stiffener_plt_len_along_web)
                    self.moment_on_stiffener_along_web = round((self.moment_on_stiffener_along_web * 10 ** -6), 3)  # kN-m

                    # shear and moment capacity calculations
                    self.shear_capa_stiffener_along_web = IS800_2007.cl_8_4_design_shear_strength(self.stiffener_plt_height_along_web *
                                                                                                  self.stiffener_plt_thick_along_web, self.stiffener_fy)
                    self.shear_capa_stiffener_along_web = round((self.shear_capa_stiffener_along_web / 1000), 3)  # kN

                    self.z_e_stiffener_along_web = (self.stiffener_plt_thick_along_web * self.stiffener_plt_height_along_web ** 2) / 6  # mm^3
                    self.moment_capa_stiffener_along_web = IS800_2007.cl_8_2_1_2_design_moment_strength(self.z_e_stiffener_along_web, 0,
                                                                                                        self.stiffener_fy, section_class='semi-compact')
                    self.moment_capa_stiffener_along_web = round((self.moment_capa_stiffener_along_web * 10 ** -6), 3)  # kN-m

                    # checks
                    if self.shear_on_stiffener_along_web > (0.6 * self.shear_capa_stiffener_along_web):
                        logger.warning("Fails in shear")
                        logger.info("Improvising thk")
                        self.stiffener_plt_thick_along_web = (math.sqrt(3) * self.gamma_m0 * self.shear_on_stiffener_along_web * 1000) / \
                                                                (self.stiffener_fy * self.stiffener_plt_height_along_web)
                        self.stiffener_plt_thick_along_web = round_up(self.stiffener_plt_thick_along_web, 2)  # mm

                        # re-calculating the moment capacity by incorporating the improvised stiffener thickness along web
                        self.z_e_stiffener_along_web = (self.stiffener_plt_thick_along_web * self.stiffener_plt_height_along_web ** 2) / 6  # mm^3
                        self.moment_capa_stiffener_along_web = IS800_2007.cl_8_2_1_2_design_moment_strength(self.z_e_stiffener_along_web, 0,
                                                                                                            self.stiffener_fy,
                                                                                                            section_class='semi-compact')
                        self.moment_capa_stiffener_along_web = round((self.moment_capa_stiffener_along_web * 10 ** -6), 3)  # kN-m

                    else:
                        pass

                    if self.moment_on_stiffener_along_web > self.moment_capa_stiffener_along_web:
                        logger.warning("Fails in moment")
                        logger.info("Improvising thk")
                        self.stiffener_plt_thick_along_web = (6 * self.gamma_m0 * self.moment_on_stiffener_along_web * 10 ** 6) / \
                                                              (self.stiffener_fy * self.stiffener_plt_height_along_web ** 2)
                        self.stiffener_plt_thick_along_web = round_up(self.stiffener_plt_thick_along_web, 2)  # mm
                    else:
                        pass
                else:
                    pass

                # shear yielding and moment capacity checks for the stiffener - across the web
                if self.stiffener_across_web == 'Yes':
                    # shear and moment demand calculations
                    self.shear_on_stiffener_across_web = ((self.sigma_max_zz + self.sigma_xx) / 2) * self.stiffener_plt_len_across_web * \
                                                        self.stiffener_plt_height_across_web
                    self.shear_on_stiffener_across_web = round((self.shear_on_stiffener_across_web / 1000), 3)  # kN

                    self.moment_on_stiffener_across_web = (self.sigma_xx * self.stiffener_plt_height_across_web * self.stiffener_plt_len_across_web ** 2 * 0.5) \
                                                         + (0.5 * self.stiffener_plt_len_across_web * (self.sigma_max_zz - self.sigma_xx) *
                                                            self.stiffener_plt_height_across_web * (2 / 3) * self.stiffener_plt_len_across_web)
                    self.moment_on_stiffener_across_web = round((self.moment_on_stiffener_across_web * 10 ** -6), 3)  # kN-m

                    # shear and moment capacity calculations
                    self.shear_capa_stiffener_across_web = IS800_2007.cl_8_4_design_shear_strength(self.stiffener_plt_height_across_web *
                                                                                                  self.stiffener_plt_thick_across_web,
                                                                                                  self.stiffener_fy)
                    self.shear_capa_stiffener_across_web = round((self.shear_capa_stiffener_across_web / 1000), 3)  # kN

                    self.z_e_stiffener_across_web = (self.stiffener_plt_thick_across_web * self.stiffener_plt_height_across_web ** 2) / 6  # mm^3
                    self.moment_capa_stiffener_across_web = IS800_2007.cl_8_2_1_2_design_moment_strength(self.z_e_stiffener_across_web, 0,
                                                                                                        self.stiffener_fy,
                                                                                                        section_class='semi-compact')
                    self.moment_capa_stiffener_across_web = round((self.moment_capa_stiffener_across_web * 10 ** -6), 3)  # kN-m

                    # checks
                    if self.shear_on_stiffener_across_web > (0.6 * self.shear_capa_stiffener_across_web):
                        logger.warning("Fails in shear")
                        logger.info("Improvising thk")
                        self.stiffener_plt_thick_across_web = (math.sqrt(3) * self.gamma_m0 * self.shear_on_stiffener_across_web * 1000) / \
                                                             (self.stiffener_fy * self.stiffener_plt_height_across_web)
                        self.stiffener_plt_thick_across_web = round_up(self.stiffener_plt_thick_across_web, 2)  # mm

                        # re-calculating the moment capacity by incorporating the improvised stiffener thickness across web
                        self.z_e_stiffener_across_web = (self.stiffener_plt_thick_across_web * self.stiffener_plt_height_across_web ** 2) / 6  # mm^3
                        self.moment_capa_stiffener_across_web = IS800_2007.cl_8_2_1_2_design_moment_strength(self.z_e_stiffener_across_web, 0,
                                                                                                             self.stiffener_fy,
                                                                                                             section_class='semi-compact')
                        self.moment_capa_stiffener_across_web = round((self.moment_capa_stiffener_across_web * 10 ** -6), 3)  # kN-m
                    else:
                        pass

                    if self.moment_on_stiffener_across_web > self.moment_capa_stiffener_across_web:
                        logger.warning("Fails in moment")
                        logger.info("Improvising thk")
                        self.stiffener_plt_thick_across_web = (6 * self.gamma_m0 * self.moment_on_stiffener_across_web * 10 ** 6) / \
                                                              (self.stiffener_fy * self.stiffener_plt_height_across_web ** 2)
                        self.stiffener_plt_thick_across_web = round_up(self.stiffener_plt_thick_across_web, 2)  # mm
                    else:
                        pass
                else:
                    pass

                # weld size at the stiffener plate
                # TODO: check the weld size at stiffener
                self.weld_size_stiffener = self.weld_size_flange  # mm

                self.weld_size_vertical_flange = self.cl_10_5_2_3_min_weld_size(self.column_tf, self.stiffener_plt_thick_along_flange)
                self.weld_size_vertical_flange = max(self.weld_size_vertical_flange, 6)  # mm

                self.weld_size_vertical_web = self.cl_10_5_2_3_min_weld_size(self.column_tw, self.stiffener_plt_thick_along_web)
                self.weld_size_vertical_web = max(self.weld_size_vertical_web, 6)  # mm

            else:
                pass

            # design of the stiffener plate between the column depth to support the outstanding stiffeners, when there are 6 anchor bolts required
            # the governing ratio is D/t_g < 29.30 (Table 2, IS 800:2007)
            if self.connectivity == 'Moment Base Plate':
                if self.tension_bolts_req == 6:
                    self.stiffener_plt_thick_btwn_D = (self.column_D - (2 * self.column_tf)) / 29.30
                    self.stiffener_plt_thick_btwn_D = round_up(self.stiffener_plt_thick_btwn_D, 2, self.column_tf)  # mm

                    if self.stiffener_plt_thick_btwn_D < self.stiffener_plt_thick_along_flange:
                        self.stiffener_plt_thick_btwn_D = self.stiffener_plt_thick_along_flange

                    self.stiffener_plt_len_btwn_D = self.column_D - (2 * self.column_tf)  # mm
                    self.stiffener_plt_height_btwn_D = self.stiffener_plt_height_along_web - 10  # mm
                else:
                    pass
            else:
                pass

            # weld checks of the stiffener welds - Combination of stresses [Reference: Cl. 10.5.10.1, IS 800:2007]

            if self.stiffener_along_flange == 'Yes':
                # Stiffener along flange - weld connecting stiffener to the base plate
                # the weld will have shear due to the bearing force and axial force due to in-plane bending of the stiffener
                f_a = (self.shear_on_stiffener_along_flange * 1000 / 2) / (0.7 * self.weld_size_stiffener * self.stiffener_plt_len_along_flange)  # MPa
                q = (self.moment_on_stiffener_along_flange * 10 ** 6 / self.stiffener_plt_height_along_flange) \
                    / (0.7 * self.weld_size_stiffener * self.stiffener_plt_len_along_flange)  # MPa
                f_e = math.sqrt(f_a ** 2 + (3 * q ** 2))  # MPa

                if f_e > ((min(self.dp_column_fu, self.dp_weld_fu_overwrite)) / (math.sqrt(3) * self.gamma_mw)):
                    self.safe = False
                    logger.warning("The weld fails in the comb check")
                    logger.info("Updating the weld size")
                else:
                    pass

            if self.stiffener_along_web == 'Yes':
                # Stiffener along web - weld connecting stiffener to the base plate
                # the weld will have shear due to the bearing force and axial force due to in-plane bending of the stiffener
                f_a = (self.shear_on_stiffener_along_web * 1000 / 2) / (0.7 * self.weld_size_stiffener * self.stiffener_plt_len_along_web)  # MPa
                q = (self.moment_on_stiffener_along_web * 10 ** 6 / self.stiffener_plt_height_along_web) \
                    / (0.7 * self.weld_size_stiffener * self.stiffener_plt_len_along_web)  # MPa
                f_e = math.sqrt(f_a ** 2 + (3 * q ** 2))  # MPa

                if f_e > ((min(self.dp_column_fu, self.dp_weld_fu_overwrite)) / (math.sqrt(3) * self.gamma_mw)):
                    self.safe = False
                    logger.warning("The weld fails in the comb check")
                    logger.info("Updating the weld size")
                else:
                    pass

            # updating the stiffener weld size if it fails in the stress combination check
            if (self.stiffener_along_flange or self.stiffener_along_web) == 'Yes':

                n = 1
                while f_e > ((min(self.dp_column_fu, self.dp_weld_fu_overwrite)) / (math.sqrt(3) * self.gamma_mw)):

                    weld_list = list(range(self.weld_size_stiffener, self.stiffener_plate_thick, 2))
                    weld_list = weld_list + [self.stiffener_plate_thick]
                    weld_list = weld_list[n - 1:]

                    for i in weld_list:
                        self.weld_size_stiffener = i
                        break

                    # choosing maximum force and minimum length and height combination for a conservative weld size
                    max_shear = max(self.shear_capa_stiffener_along_flange, self.shear_on_stiffener_along_web)
                    max_moment = max(self.moment_on_stiffener_along_flange, self.moment_on_stiffener_along_web)
                    min_len = min(self.stiffener_plt_len_along_flange, self.stiffener_plt_len_along_web)
                    min_height = min(self.stiffener_plt_height_along_flange, self.stiffener_plt_height_along_web)

                    f_a = (max_shear * 1000 / 2) / (0.7 * self.weld_size_stiffener * min_len)  # MPa
                    q = (max_moment * 10 ** 6 / min_height) / (0.7 * self.weld_size_stiffener * min_len)  # MPa
                    f_e = math.sqrt(f_a ** 2 + (3 * q ** 2))  # MPa

                    n += 1

                    self.weld_size_stiffener = i

                    if n > len(weld_list):
                        logger.warning("The max weld size is ")
                        logger.error("Cannot compute weld size")
                        break

        elif self.connectivity == 'Hollow/Tubular Column Base':  # TODO: add condition when required
            pass

        # end of calculation
        if self.safe:
            self.design_status = True
            logger.info(": Overall base plate connection design is safe")
            logger.debug(": =========End Of design===========")
        else:
            logger.info(": Overall base plate connection design is unsafe")
            logger.debug(": =========End Of design===========")

        # printing values for output dock
        # anchor bolt
        print(self.anchor_dia_provided)
        print(self.anchor_grade)
        print(self.anchor_length_provided)  # Length (mm)
        print(self.shear_capacity_anchor)
        print(self.bearing_capacity_anchor)
        print(self.anchor_capacity)  # Bolt capacity (kN)
        print(self.combined_capacity_anchor)  # Combined capacity (kN)
        if self.connectivity == 'Moment Base Plate':
            print(self.tension_capacity_anchor)  # Tension capacity (kN) (show only for 'Gusseted Base Plate' connectivity)
        else:
            pass

        # anchor bolt for uplift (this case is applicable only when self.load_axial_tension > 0 or when connectivity is gusseted bp)
        if self.connectivity == 'Moment Base Plate':
            print(self.anchor_dia_uplift)
            print(self.anchor_grade_tension)
            print(self.anchor_length_provided)
            print(self.tension_capacity_anchor_uplift)

        # base plate
        print(self.plate_thk)  # Thickness (mm)
        print(self.bp_length_provided)  # Length (mm)
        print(self.bp_width_provided)  # Width (mm)

        # Gusset Plate (this section and subsection is only for 'Gusseted Base Plate' connectivity)

        # details coming soon...

        # detailing
        print(self.anchor_nos_provided)
        print(self.pitch_distance)  # Pitch Distance (mm) (show only when this value is not 'Null')
        print(self.gauge_distance)  # Gauge Distance (mm) mm (show only when this value is not 'Null')
        print(self.end_distance)  # mm
        print(self.edge_distance)  # mm
        if self.connectivity == 'Welded Column Base':
            print(self.projection)  # mm (show only for 'Welded-Slab Base' connectivity)
        else:
            pass

        # Gusset/Stiffener Plate
        # Details tab (this is supposed to be taken from Osdag 2 - details to be given soon)

        # Stiffener plate along flange
        if self.stiffener_along_flange == 'Yes':
            print(self.stiffener_plt_thick_along_flange)
            print(self.shear_on_stiffener_along_flange)
            print(self.shear_capa_stiffener_along_flange)
            print(self.moment_on_stiffener_along_flange)
            print(self.moment_capa_stiffener_along_flange)
        else:
            pass

        # Stiffener plate along web
        if self.stiffener_along_web == 'Yes':
            print(self.stiffener_plt_thick_along_web)
            print(self.shear_on_stiffener_along_web)
            print(self.shear_capa_stiffener_along_web)
            print(self.moment_on_stiffener_along_web)
            print(self.moment_capa_stiffener_along_web)
        else:
            pass

        # Stiffener across web
        if self.stiffener_across_web == 'Yes':
            print(self.stiffener_plt_thick_across_web)
            print(self.shear_on_stiffener_across_web)
            print(self.shear_capa_stiffener_across_web)
            print(self.moment_on_stiffener_across_web)
            print(self.moment_capa_stiffener_across_web)
        else:
            pass

        # Weld

        print(self.weld_size_flange if self.weld_type != 'Butt Weld' else '')  # Size at Flange (mm)
        print(self.weld_size_web if self.weld_type != 'Butt Weld' else '')  # Size at Web (mm)

        if self.stiffener_along_flange == 'Yes':
            print(self.weld_size_stiffener if self.weld_type != 'Butt Weld' else '')  # weld size at stiffener along flange (mm)

        if self.stiffener_along_web == 'Yes':
            print(self.weld_size_stiffener if self.weld_type != 'Butt Weld' else '')  # weld size at stiffener along web (mm)

        if self.stiffener_across_web == 'Yes':
            print(self.weld_size_stiffener if self.weld_type != 'Butt Weld' else '')  # weld size at stiffener along web (mm)

        # this might not be required
        # print(self.weld_size if self.weld_type != 'Butt Weld' else '')  # Weld size (mm)

        # col properties
        print(self.column_D, self.column_bf, self.column_tf, self.column_tw, self.column_r1, self.column_r2)
        # print(self.w)
