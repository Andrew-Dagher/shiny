from shiny import App, ui
from modules.sidebar_module import sidebar_ui, sidebar_server
from modules.dashboard_module import dashboard_ui, dashboard_server
from modules.group_performance_module import (
    group_performance_ui,
    group_performance_server,
)
from database.load_data import initialize_database

# initialize the SQLite database and load the CSV data
initialize_database()

# define the UI
app_ui = ui.page_fluid(
    ui.h1("Insurance Performance Dashboard"),
    ui.layout_sidebar(
        sidebar_ui("sidebar"),
        ui.navset_tab(
            dashboard_ui("dashboard"),
            group_performance_ui("group_performance"),
        ),
    ),
)

# define the server logic
def app_server(input, output, session):
    filtered_data = sidebar_server("sidebar")
    dashboard_server("dashboard", filtered_data)
    group_performance_server("group_performance", filtered_data)

# launch the app
app = App(app_ui, app_server)
