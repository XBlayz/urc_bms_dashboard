import dearpygui.dearpygui as dpg

def setup_dpg_mock_controller(generator):
    """
    Initializes the DearPyGui UI using a direct object reference.
    Does NOT start the blocking DPG event loop.
    """
    dpg.create_context()

    # Callbacks directly invoke the generator's methods
    def cb_connect():
        generator.connect_bms()

    def cb_disconnect():
        generator.disconnect_bms()

    def cb_rate_changed(sender, app_data, user_data):
        # user_data is the group name ("fast", "medium", "slow")
        # app_data is the float value from the slider
        generator.set_update_rate(user_data, float(app_data))

    with dpg.window(tag="Main", label="BMS Mock Director", width=400, height=350, no_close=True, no_collapse=True):
        dpg.add_text("Connection Control", color=[150, 200, 255])

        with dpg.group(horizontal=True):
            dpg.add_button(label="Connect BMS", width=180, height=40, callback=cb_connect)
            dpg.add_button(label="Disconnect BMS", width=180, height=40, callback=cb_disconnect)

        dpg.add_separator()
        dpg.add_spacing(count=5)

        dpg.add_text("Update Frequencies (Hz)", color=[150, 200, 255])
        dpg.add_slider_float(label=" Fast (Cells)", default_value=20.0, min_value=1.0, max_value=100.0, callback=cb_rate_changed, user_data="fast")
        dpg.add_slider_float(label=" Medium (Pack)", default_value=5.0, min_value=1.0, max_value=50.0, callback=cb_rate_changed, user_data="medium")
        dpg.add_slider_float(label=" Slow (FSM/Diag)", default_value=1.0, min_value=0.1, max_value=10.0, callback=cb_rate_changed, user_data="slow")

    dpg.create_viewport(title='Advanced Mock Controller', width=420, height=380)
    dpg.setup_dearpygui()
    dpg.show_viewport()
