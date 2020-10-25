class SwhLabels(object):
    """Maps input and output database labels
    to short labels used in the mswh analysis code.

    Units:

    If not otherwise indicated in the labels, assume SI units.
    """

    def __init__(self):
        pass

    def set_hous_labels(self):
        """Household related labels"""

        self.cons_l = {
            "id": "Consumer ID",
            "ld_id": "Load ID",
            "occ": "Occupancy",
            "pr_occ": "Project Occupancy",
            "at_hm": "At Home",
            "housing_typ": "Housing Type",
            "tilt_mean": "Tilt Mean",
            "tilt_std_dev": "Tilt Standard Deviation",
            "tilt": "Tilt",
            "azim_mean": "Azimuth Mean",
            "azim_std_dev": "Azimuth Standard Deviation",
            "azim": "Azimuth",
            "load": "End-Use Load [gal]",
            "load_m3": "End-Use Load",
            "max_load": "Peak End-Use Load [gal]",
            "dem_estimate": "Demand Estimate [GPD]",
            # weather data column labels
            "t_amb_C": "dry_bulb_C",
            "t_amb_F": "dry bulb",
            "t_amb": "Temperature - Ambient",
            "t_wet_bulb_C": "wet_bulb_C",
            "irrad_on_tilt": "global_tilt_radiation_Wm2",
            "t_main_C": "water_main_t_C",
            "t_main_F": "water_main_t_F",
            "rel_hum": "rhum (%)",
            "t_main": "Temperature - Water Main",
            "season": "season",
            "summer": "summer",
            "winter": "winter",
            "month": "month",
            "day": "day",
            "hour": "hour",
            "wea_wat": "Weather/Water Main",
            "exmp_loads": "example_loads",
            "exmp_consload": "example_consloadid_list",
            # only if not loading in the precalculated example loads
            # 'tank_sz_for_loads': 'Gas Tank Size for Load Calc',
            # 'tank_sz_for_loads_gal': 'Gas Tank Size for Load Calc [gal]',
            "gas": "Gas",
            "el": "Electricity",
            "disc_rt": "Discount Rate",
            "s_tax": "Sales Tax",
        }

        return self.cons_l

    def set_prod_labels(self):
        """Solar water heating system related labels"""

        self.sys_l = {
            "sys_id": "System ID",
            "sys": "System",
            "sys_desr": "System Description",
            "comp_id": "Component ID",
            "comp": "Component",
            "comp_tech": "Component Technology",
            "comp_func": "Component Function",
            "retro": "Retrofit",
            # components
            "sol_col": "solar collector",
            "pv": "photovoltaic",
            "inv": "inverter",
            "hp": "heat pump",
            "hp_tank": "heat pump tank",
            "the_sto": "thermal storage tank",
            "sol_tank": "solar storage tank",
            "gas_tank": "gas tank WH",
            "bat_sto": "battery storage",
            "el_res": "electric resistance",
            "gas_burn": "gas burner",
            "dist_pump": "distribution pump",
            "sol_pump": "solar pump",
            "piping": "piping",
            # systems
            "gas_tank_wh": "gas tank wh",
            "solar_thermal_retrofit": "solar thermal retrofit",
            "solar_thermal_new": "solar thermal new",
            "solar_electric": "solar electric",
            "bckp": "backup",
            "solar": "solar",
            # sizing
            "cap": "Component Size",
            "cap_unit": "Component Size Unit",
            "discr_size": "Discrete Size",
            # performance parameters
            "param": "Performance Parameter",
            "param_value": "Performance Parameter Value",
            "param_unit": "Performance Parameter Unit",
            "interc_hwb": "interc hwb",
            "interc_cd": "interc cd",
            "slope_hwb": "slope hwb",
            "a1_cd": "a1 cd",
            "a2_cd": "a2 cd",
            "eta": "efficiency",
            "eta_el_res": "electric resistance efficiency",
            "eta_pv": "PV efficiency",
            "eta_dc_ac": "DC to AC efficiency",
            "eta_sol_pump": "nominal distribution pump efficiency",
            "eta_dist_pump": "nominal solar pump efficiency",
            "f_act": "fraction of active PV area",
            "irrad_ref": "reference irradiation",
            "cop_rated": "rated COP",
            "heat_cap_rated": "rated heating capacity",
            "aux_heat_cap": "auxiliary heater capacity",
            "c1_cop": "c1_cop",
            "c2_cop": "c2_cop",
            "c3_cop": "c3_cop",
            "c4_cop": "c4_cop",
            "c5_cop": "c5_cop",
            "c6_cop": "c6_cop",
            "c1_heat_cap": "c1_heat_cap",
            "c2_heat_cap": "c2_heat_cap",
            "c3_heat_cap": "c3_heat_cap",
            "c4_heat_cap": "c4_heat_cap",
            "c5_heat_cap": "c5_heat_cap",
            "c6_heat_cap": "c6_heat_cap",
            "ins_thi": "insulation thickness",
            "h_vs_r": "height vs. radius",
            "spec_hea_con": "specific heat conductivity",
            "f_upper_vol": "upper volume fraction",
            "dt_appr": "temperature difference (approach)",
            "t_max_tank": "maximum temperature",
            "t_tap_set": "tap temperature setpoint",
            "eta_coil": "coil efficiency",
            "circ": "circulation",
            "long_br_len_fr": "longest branch length fraction",
            "comb_eff": "combustion efficiency",
            "tank_re": "tank recovery efficiency",
            "ave_eta": "Average Efficiency",
            "pipe_spec_hea_con": "piping insulation specific heat conductivity",
            "dia_len_sca": "diameter vs. length scaler",
            "dia_len_exp": "diameter vs. length exponent",
            "pipe_ins_thick": "piping insulation thickness",
            "discr_diam_m": "discrete diameters",
            "sng_fml_attch": "single-family attached scaler",
            "sng_fml_dtch": "single-family detached scaler",
            "pipe_pr_mult": "piping pricing multiplier",
            "pipe_pr_exp": "piping pricing exponent",
            "diam": "Pipe Diameter",
            "flow_factor": "flow factor",
            # to apply regressions
            # (assign prices or sizes)
            "function_of": "Function Of",
            "fit_type": "Fit",
            "fit_params": "Fit Parameters",
            "comp_size_fit_params": "Component Size Fit Parameters",
            "comp_price_fit_params": "Retail Price Fit Parameters",
            # input table names
            "sys_assign_bc": "sysassign_basecase",
            "sys_assign_pc": "sysassign_policy_case",
            "comp_perf": "component_performance",
            "comp_sizing": "comp_1_sizing_regression",
            "comp_pricing": "comp_2_pricing_regression",
            "sys_list": "sys_1_system_list",
            "comp_list": "sys_3_components",
            "dia_len_slope": "diameter vs. length slope",
            "dia_len_interc": "diameter vs. length intercept",
        }

        return self.sys_l

    def set_res_labels(self):
        """Labels for any calculation output.

        For annual summaries, temperatures are averaged
        and heat gains summed.
        """

        self.res_l = {
            "use": "Use",
            "sav": "Savings",
            "ht": "Heat",
            # annual energy use
            "gas_use": "Energy Use - Gas",
            "gas_use_s": "Energy Use - Gas, Summer",
            "gas_use_w": "Energy Use - Gas, Winter",
            "el_use": "Energy Use - Electricity",
            "grs_el_use": "Energy Use - Electricity Before PV",
            "el_use_s": "Energy Use - Electricity, Summer",
            "el_use_w": "Energy Use - Electricity, Winter",
            "gas_use_no_dist": "Energy Use - Gas, w/o Dist Loss",
            "gas_use_s_no_dist": "Energy Use - Gas, Summer, w/o Dist Loss",
            "gas_use_w_no_dist": "Energy Use - Gas, Winter, w/o Dist Loss",
            # annual energy savings
            "gas_sav": "Energy Savings - Gas",
            "gas_sav_s": "Energy Savings - Gas, Summer",
            "gas_sav_w": "Energy Savings - Gas, Winter",
            "el_sav": "Energy Savings - Electricity",
            "el_sav_s": "Energy Savings - Electricity, Summer",
            "el_sav_w": "Energy Savings - Electricity, Winter",
            "gas_sav_no_dist": "Energy Savings - Gas, w/o Dist Loss",
            "gas_sav_s_no_dist": "Energy Savings - Gas, Summer, w/o Dist Loss",
            "gas_sav_w_no_dist": "Energy Savings - Gas, Winter, w/o Dist Loss",
            "dist_loss_substring": ", w/o Dist Loss",
            "sol_fra": "Solar Fraction",
            "month_sol_fra": "Monthly Solar Fraction",
            "season_sol_fra": "Seasonal Solar Fraction",
            "proj_load": "Project End-Use Load",  # m3
            "q_dem": "Net Heat Demand",
            "q_dem_tot": "Heat Demand With Dist. Loss",
            # here sys refers to the main system without the backup
            "q_del_tank": "Tank Heat Delivered",
            "q_del_bckp": "Backup Heat Delivered",
            "q_del": "Total Heat Delivered",
            "q_dist_loss": "Distribution Heat Loss",
            "q_dist_loss_at_bckp": "Distribution Heat Loss at Backup",
            "q_dist_loss_at_bckp_sum": "Distribution Heat Loss at Backup, Summer",
            "q_dist_loss_at_bckp_win": "Distribution Heat Loss at Backup, Winter",
            "q_unmet_tank": "Tank Unmet Heat",
            "q_unmet": "Unmet Heat",
            "q_dump": "Dumped Heat",
            "q_del_sol": "Solar Heat Delivered To Tank",
            "q_del_hp": "Heat Pump Gain Delivered To Tank",
            "q_del_aux": "Auxiliary Heat Delivered To Tank",
            "p_pv_ac": "PV Generated Power",
            "p_pv_dc": "PV Generated Power (without inverter)",
            "p_hp_el_use": "Electricity Use - Heat Pump",
            "p_el_res_use": "Electricity Use - Electric Resistance Heater",
            "p_pv_to_hp": "Electricity Use - PV to Heat Pump",
            "p_pv_to_el_res": "Electricity Use - PV to Electric Resistance",
            "p_surplus": "Available PV Electricity",
            "t_tank_up": "Temperature - Upper Tank Volume",
            "t_tank_low": "Temperature - Lower Tank Volume",
            "t_coil_out": "Temperature - Tank Coil Out",
            "t_set": "Temperature - Hot Water Set",
            "t_main": "Temperature - Main Water",
            "t_amb": "Temperature - Ambient Air (Dry Bulb)",
            "t_wet_bulb": "Temperature - Ambient Air (Wet Bulb)",
            "q_loss_up": "Heat Loss - Upper Tank Volume",
            "q_loss_low": "Heat Loss - Lower Tank Volume",
            "q_ovrcool_tank": "Tank Overcool (Heat Rate)",
            "q_dem_balance": "Demand Balancing Error (Heat Rate)",
            "dt_dist": "Temperature Drop in Distribution Pipes",
            "flow_on_frac": "Flow On Fraction",
        }

        return self.res_l
