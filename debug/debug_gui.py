import dearpygui.dearpygui as dpg

def setup_dpg_mock_controller(generator):
    dpg.create_context()

    def cb_charging_params():
        v = dpg.get_value("charge_v")
        c = dpg.get_value("charge_c")
        generator.set_charging_params(v, c)

    def cb_actuator(sender, app_data, user_data):
        val_map = {"Auto": 0, "Force Off": 1, "Force On": 2}
        generator.set_actuator_override(user_data, val_map[app_data])

    with dpg.window(tag="Main", label="BMS Mock Director", width=400, height=600, no_close=True, no_collapse=True):
        dpg.add_text("Connection Control", color=[150, 200, 255])

        with dpg.group(horizontal=True):
            dpg.add_button(label="Connect BMS", width=180, height=30, callback=lambda: generator.connect_bms())
            dpg.add_button(label="Disconnect BMS", width=180, height=30, callback=lambda: generator.disconnect_bms())

        dpg.add_separator()
        dpg.add_spacer(height=5)

        dpg.add_text("FSM & State Overrides", color=[150, 200, 255])
        dpg.add_checkbox(label="External SDC Enabled", default_value=True, callback=lambda s, a: generator.set_external_sdc(a))
        dpg.add_checkbox(label="Force INITIALIZING (No Telemetry)", callback=lambda s, a: generator.set_force_initializing(a))
        dpg.add_slider_int(label="Force Error Code", default_value=0, min_value=0, max_value=255, callback=lambda s, a: generator.set_forced_error(int(a)))

        dpg.add_separator()
        dpg.add_spacer(height=5)

        dpg.add_text("Charging Settings", color=[150, 200, 255])
        dpg.add_slider_float(tag="charge_v", label="Voltage (V)", default_value=400.0, min_value=0.0, max_value=600.0, callback=cb_charging_params)
        dpg.add_slider_float(tag="charge_c", label="Current (A)", default_value=30.0, min_value=0.0, max_value=100.0, callback=cb_charging_params)

        dpg.add_separator()
        dpg.add_spacer(height=5)

        dpg.add_text("Actuators Override", color=[150, 200, 255])
        act_opts = ["Auto", "Force Off", "Force On"]
        with dpg.group(horizontal=False):
            dpg.add_combo(act_opts, default_value="Auto", label="AIR +", user_data="air_pos", callback=cb_actuator, width=120)
            dpg.add_combo(act_opts, default_value="Auto", label="AIR -", user_data="air_neg", callback=cb_actuator, width=120)
            dpg.add_combo(act_opts, default_value="Auto", label="Pre-Charge", user_data="pre_charge", callback=cb_actuator, width=120)
            dpg.add_combo(act_opts, default_value="Auto", label="SDC", user_data="sdc", callback=cb_actuator, width=120)

        dpg.add_separator()
        dpg.add_spacer(height=5)

        dpg.add_text("Update Frequencies (Hz)", color=[150, 200, 255])
        dpg.add_slider_float(label=" Fast (Cells)", default_value=10.0, min_value=1.0, max_value=100.0, callback=lambda s, a: generator.set_update_rate("fast", float(a)))
        dpg.add_slider_float(label=" Medium (Pack)", default_value=5.0, min_value=1.0, max_value=50.0, callback=lambda s, a: generator.set_update_rate("medium", float(a)))
        dpg.add_slider_float(label=" Slow (FSM/Diag)", default_value=1.0, min_value=0.1, max_value=10.0, callback=lambda s, a: generator.set_update_rate("slow", float(a)))

    dpg.create_viewport(title='Advanced Mock Controller', width=420, height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
