import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# Use a dark Plotly theme for all charts
plotly_template = "plotly_dark"

# ==============================================================================
#  1. DATA LOADING & PREPARATION
# ==============================================================================
try:
    races = pd.read_csv('data/races.csv')
    results = pd.read_csv('data/results.csv')
    drivers = pd.read_csv('data/drivers.csv')
    constructors = pd.read_csv('data/constructors.csv')
    circuits = pd.read_csv('data/circuits.csv')

    drivers['driver_name'] = drivers['forename'] + ' ' + drivers['surname']
    
    df = results.merge(
        races[['raceId', 'year', 'name', 'circuitId']].rename(columns={'name': 'name_race'}), 
        on='raceId'
    )
    df = df.merge(
        drivers[['driverId', 'driver_name', 'nationality']], 
        on='driverId'
    )
    df = df.merge(
        constructors[['constructorId', 'name', 'nationality']].rename(columns={'name': 'name_constructor'}),
        on='constructorId', 
        suffixes=('_driver', '_constructor')
    )
    df = df.merge(
        circuits[['circuitId', 'name', 'country']].rename(columns={'name': 'name_circuit'}),
        on='circuitId'
    )

    df['position'] = pd.to_numeric(df['position'], errors='coerce')
    df['points'] = pd.to_numeric(df['points'], errors='coerce')
    df['grid'] = pd.to_numeric(df['grid'], errors='coerce')

    
    winners = df[df['position'] == 1]
    podiums = df[df['position'].isin([1, 2, 3])]
    poles = df[df['grid'] == 1]
    
    constructor_points = df.groupby(['year', 'name_constructor'])['points'].sum().reset_index()
    driver_points = df.groupby(['year', 'driver_name'])['points'].sum().reset_index()
    
    min_year = df['year'].min()
    max_year = df['year'].max()
    
    all_drivers = sorted(df['driver_name'].unique())
    all_constructors = sorted(df['name_constructor'].unique())
    all_circuits = sorted(df['name_circuit'].unique())

except FileNotFoundError as e:
    print(f"Error: {e}")
    print("="*50)
    print("ERROR: Data files not found.")
    print("Please make sure you have unzipped all 14 CSV files")
    print("from the Kaggle dataset into the 'data/' directory.")
    print("="*50)
    df = pd.DataFrame(columns=['year', 'driver_name', 'name_constructor', 'points', 'position', 'name_race', 'country', 'driverId', 'constructorId', 'name_circuit', 'nationality_driver', 'nationality_constructor', 'grid'])
    winners = pd.DataFrame(columns=['year', 'driver_name', 'name_constructor', 'nationality_driver', 'nationality_constructor', 'name_circuit', 'grid'])
    podiums = pd.DataFrame(columns=['year', 'driver_name', 'name_constructor', 'position'])
    poles = pd.DataFrame(columns=['year', 'driver_name', 'name_constructor', 'name_circuit', 'grid'])
    constructor_points = pd.DataFrame(columns=['year', 'name_constructor', 'points'])
    driver_points = pd.DataFrame(columns=['year', 'driver_name', 'points'])
    min_year, max_year = 1950, 2024
    all_drivers, all_constructors, all_circuits = [], [], []

# ==============================================================================
#  2. APP INITIALIZATION
# ==============================================================================
assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    assets_folder=assets_path
)
server = app.server
app.title = "F1 Analytics Dashboard"

# ==============================================================================
#  3. KPI CARD CREATION
# ==============================================================================
def create_kpi_card(title, value, id_name):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(title, className="card-title"),
                html.P(f"{value:,}", className="card-body", id=id_name),
            ]
        ),
        className="kpi-card",
    )

# ==============================================================================
#  4. APP LAYOUT (All descriptions added)
# ==============================================================================
app.layout = dbc.Container(
    [
        # --- HEADER ---
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Img(
                            src='https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/F1.svg/320px-F1.svg.png',
                            className='header-logo'
                        ),
                        html.H1("Formula 1 Interactive Analytics Dashboard"),
                    ],
                    className="header",
                )
            )
        ),
        
        # --- YEAR SLIDER FILTER ---
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H5("Filter by Year"),
                        # --- NEW: Added text to show the selected year range ---
                        html.H5(
                            id='selected-year-range-text', 
                            style={'textAlign': 'center', 'marginTop': '10px', 'color': '#E10600'}
                        ),
                        dcc.RangeSlider(
                            id='year-slider',
                            min=min_year,
                            max=max_year,
                            value=[max_year - 20, max_year], 
                            marks={str(y): str(y) for y in range(min_year, max_year + 1, 5)},
                            step=1,
                            className="Slider"
                        ),
                    ],
                    className="graph-container",
                ),
                width=12,
                style={'margin-top': '20px'}
            )
        ),
        
        # --- TABS ---
        dcc.Tabs(
            id="dashboard-tabs",
            value="tab-overview",
            className="Tabs",
            children=[
                # =================== OVERVIEW TAB ===================
                dcc.Tab(
                    label="Overview",
                    value="tab-overview",
                    className="Tab",
                    selected_className="Tab--selected",
                    children=[
                        # --- KPIs ---
                        dbc.Row(
                            [
                                dbc.Col(create_kpi_card("Total Races", 0, 'kpi-races'), md=4),
                                dbc.Col(create_kpi_card("Total Drivers", 0, 'kpi-drivers'), md=4),
                                dbc.Col(create_kpi_card("Total Constructors", 0, 'kpi-constructors'), md=4),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        # --- Row 1 ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Races Per Season"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This bar chart shows the total number of F1 races held in each season. It helps visualize the expansion or contraction of the F1 calendar within the selected period.", className="graph-description"),
                                            dcc.Graph(id='races-per-season-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Races By Country (Top 15)"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This chart displays the top 15 countries that have hosted the most F1 races. It highlights the historical and modern centers of Grand Prix racing.", className="graph-description"),
                                            dcc.Graph(id='races-by-country-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        
                        # --- Row 2 ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Winning Constructors by Nationality"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This pie chart breaks down all race wins by the constructor's registered nationality. It shows the dominant nations in F1 engineering, such as Italy (Ferrari), the UK (McLaren, Williams), and Austria (Red Bull).", className="graph-description"),
                                            dcc.Graph(id='constructor-nat-pie') 
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Wins by Driver Nationality"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This bar chart shows the total number of wins achieved by drivers from the top 15 most successful nationalities. It highlights which countries have produced the most winning drivers.", className="graph-description"),
                                            dcc.Graph(id='driver-nat-bar') 
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        
                        # --- Row 3 ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Drivers by Pole Positions"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This chart counts the drivers who have started a race from P1 (grid position 1) most often. A pole position is a key performance metric for qualifying speed.", className="graph-description"),
                                            dcc.Graph(id='driver-poles-chart') 
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Constructors by Pole Positions"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This chart shows the 15 teams whose cars have secured P1 starts most frequently. It's a strong indicator of a car's single-lap qualifying performance.", className="graph-description"),
                                            dcc.Graph(id='constructor-poles-chart') 
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                    ]
                ),
                
                # =================== DRIVER TAB ===================
                dcc.Tab(
                    label="Driver Analytics",
                    value="tab-drivers",
                    className="Tab",
                    selected_className="Tab--selected",
                    children=[
                        # --- Row 1 ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Driver Cumulative Wins Over Time"),
                                            # --- MODIFIED: Description moved up ---
                                            html.P("This line chart tracks the running total of career wins for the selected drivers, year by year. It's perfect for comparing the career trajectories of different drivers across eras.", className="graph-description"),
                                            html.Label("Select Drivers (up to 10):"), 
                                            dcc.Dropdown(
                                                id='driver-dropdown',
                                                options=[{'label': d, 'value': d} for d in all_drivers],
                                                value=['Lewis Hamilton', 'Max Verstappen', 'Michael Schumacher'],
                                                multi=True,
                                                className="Dropdown" 
                                            ),
                                            dcc.Graph(id='driver-wins-over-time-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Driver Points per Season"),
                                            # --- MODIFIED: Description moved up ---
                                            html.P("This chart compares the total points scored by the same selected drivers in each individual season. It helps identify a driver's peak seasons and periods of dominance.", className="graph-description"),
                                            html.Label("Updates based on drivers from left chart"),
                                            dcc.Graph(id='driver-points-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        # --- Row 2 ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Drivers by Wins (Selected Years)"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This bar chart ranks the 15 drivers who have achieved the most race victories within the selected year range. This shows who was most dominant during a specific period.", className="graph-description"),
                                            dcc.Graph(id='driver-wins-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Drivers by Podiums (Selected Years)"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This chart shows the 15 drivers with the most podium finishes (1st, 2nd, or 3rd). This metric is a strong indicator of consistent high-level performance, not just wins.", className="graph-description"),
                                            dcc.Graph(id='podiums-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                    ]
                ),
                
                # =================== CONSTRUCTOR TAB ===================
                dcc.Tab(
                    label="Constructor Analytics",
                    value="tab-constructors",
                    className="Tab",
                    selected_className="Tab--selected",
                    children=[
                        # --- Row 1 ---
                         dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Constructor Cumulative Wins Over Time"),
                                            # --- MODIFIED: Description moved up ---
                                            html.P("This chart tracks the running total of all-time wins for the selected constructors. It clearly illustrates the long-term success and legacy of F1's most iconic teams.", className="graph-description"),
                                            html.Label("Select Constructors (up to 10):"),
                                            dcc.Dropdown(
                                                id='constructor-dropdown',
                                                options=[{'label': c, 'value': c} for c in all_constructors],
                                                value=['Ferrari', 'Mercedes', 'Red Bull'],
                                                multi=True,
                                                className="Dropdown" 
                                            ),
                                            dcc.Graph(id='constructor-wins-over-time-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Constructor Points per Season"),
                                            # --- MODIFIED: Description moved up ---
                                            html.P("This chart shows the total points scored by the selected constructors in each season. It's useful for seeing the impact of rule changes or the rise and fall of dominant teams.", className="graph-description"),
                                            html.Label("Updates based on constructors from left chart"),
                                            dcc.Graph(id='constructor-points-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        # --- Row 2 ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Constructors by Wins (Selected Years)"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This bar chart ranks the 15 teams that have achieved the most race victories within the selected year range. This highlights the most dominant teams of a given era.", className="graph-description"),
                                            dcc.Graph(id='constructor-wins-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6 
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Constructors by Podiums (Selected Years)"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This chart shows the 15 teams with the most podium finishes. It identifies constructors who consistently built competitive cars, even if they didn't always win.", className="graph-description"),
                                            dcc.Graph(id='constructor-podiums-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                    ]
                ),

                # =================== CIRCUIT TAB ===================
                dcc.Tab(
                    label="Circuit Analytics",
                    value="tab-circuits",
                    className="Tab",
                    selected_className="Tab--selected",
                    children=[
                        # --- Row 1 ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Circuits by Race Count"),
                                            # --- MODIFIED: Expanded Description ---
                                            html.P("This chart shows the 15 circuits that have hosted the most F1 races. It highlights the classic, most-visited tracks in F1 history (e.g., Monza, Silverstone).", className="graph-description"),
                                            dcc.Graph(id='top-circuits-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 10 Winningest Drivers at Selected Circuit"),
                                            # --- MODIFIED: Description moved up ---
                                            html.P("This chart shows the 10 drivers with the most wins at the single circuit selected below. This can reveal 'circuit specialists' who excelled at a particular track.", className="graph-description"),
                                            html.Label("Select a Circuit:"),
                                            dcc.Dropdown(
                                                id='circuit-dropdown',
                                                options=[{'label': c, 'value': c} for c in all_circuits],
                                                value='Autodromo Nazionale di Monza',
                                                multi=False, 
                                                className="Dropdown"
                                            ),
                                            dcc.Graph(id='circuit-races-over-time-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        # --- Row 2 ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 10 Winningest Constructors at Selected Circuit"),
                                            # --- MODIFIED: Description moved up ---
                                            html.P("This chart shows the 10 teams with the most wins at the selected circuit. It highlights which constructors built cars that were historically dominant at that track.", className="graph-description"),
                                            html.Label("Updates based on circuit from chart above"),
                                            dcc.Graph(id='constructor-wins-at-circuit-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 10 Drivers by Pole Position at Selected Circuit"),
                                            # --- MODIFIED: Description moved up ---
                                            html.P("This chart shows the 10 drivers with the most pole positions at the selected circuit. This identifies drivers who were exceptionally fast over one lap at that track.", className="graph-description"),
                                            html.Label("Updates based on circuit from chart above"),
                                            dcc.Graph(id='driver-poles-at-circuit-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                    ]
                ),
            ]
        ),
    ],
    fluid=True,
)

# ==============================================================================
#  5. INTERACTIVITY (CALLBACKS)
# ==============================================================================

# --- Helper function for empty charts ---
def create_empty_figure(message):
    fig = go.Figure()
    fig.update_layout(
        template=plotly_template,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[
            {
                'text': message,
                'showarrow': False,
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'font': {'size': 16, 'color': 'white'}
            }
        ]
    )
    return fig

# --- Main Callback for all year-slider-based charts ---
@app.callback(
    [
        # KPIs
        Output('kpi-races', 'children'),
        Output('kpi-drivers', 'children'),
        Output('kpi-constructors', 'children'),
        # --- NEW: Year Range Text ---
        Output('selected-year-range-text', 'children'),
        # Overview Tab
        Output('races-per-season-chart', 'figure'),
        Output('races-by-country-chart', 'figure'),
        Output('constructor-nat-pie', 'figure'),
        Output('driver-nat-bar', 'figure'),
        Output('driver-poles-chart', 'figure'),        
        Output('constructor-poles-chart', 'figure'),   
        # Driver Tab
        Output('driver-wins-chart', 'figure'),
        Output('podiums-chart', 'figure'),
        # Constructor Tab
        Output('constructor-wins-chart', 'figure'),
        Output('constructor-podiums-chart', 'figure'), 
        # Circuit Tab
        Output('top-circuits-chart', 'figure'),
    ],
    [Input('year-slider', 'value')]
)
def update_overview_graphs(year_range):
    # Filter all relevant dataframes
    dff = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]
    winners_dff = winners[(winners['year'] >= year_range[0]) & (winners['year'] <= year_range[1])]
    podiums_dff = podiums[(podiums['year'] >= year_range[0]) & (podiums['year'] <= year_range[1])]
    poles_dff = poles[(poles['year'] >= year_range[0]) & (poles['year'] <= year_range[1])] 

    # --- KPIs ---
    kpi_races_val = f"{dff['raceId'].nunique():,}"
    kpi_drivers_val = f"{dff['driverId'].nunique():,}"
    kpi_constructors_val = f"{df['constructorId'].nunique():,}"

    # --- NEW: Year Range Text ---
    # Using an en-dash '–' for a cleaner look
    year_range_text = f"Showing Data For: {year_range[0]} – {year_range[1]}"

    # --- Races Per Season ---
    races_per_season = dff.groupby('year')['raceId'].nunique().reset_index()
    fig_races_season = px.bar(races_per_season, x='year', y='raceId', title="Total Races Each Season", template=plotly_template)
    fig_races_season.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Number of Races")
    fig_races_season.update_traces(marker_color='#E10600')

    # --- Races By Country ---
    races_by_country = dff.groupby('country')['raceId'].nunique().reset_index().nlargest(15, 'raceId')
    fig_races_country = px.bar(races_by_country.sort_values('raceId', ascending=True), x='raceId', y='country', orientation='h', title="Top 15 Host Countries", template=plotly_template)
    fig_races_country.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Country", xaxis_title="Number of Races")
    fig_races_country.update_traces(marker_color='#E10600')

    # --- Constructor Nationality Pie ---
    constructor_nat = winners_dff.groupby('nationality_constructor')['raceId'].count().reset_index().rename(columns={'raceId': 'wins'})
    fig_pie_constructor_nat = px.pie(
        constructor_nat, 
        names='nationality_constructor', 
        values='wins', 
        title="Win % by Constructor Nationality",
        template=plotly_template,
        color_discrete_sequence=px.colors.sequential.Reds 
    )
    fig_pie_constructor_nat.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05] * len(constructor_nat))
    fig_pie_constructor_nat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, legend_title="Nationality")

    # --- Driver Nationality Bar ---
    driver_nat = winners_dff.groupby('nationality_driver')['raceId'].count().reset_index().rename(columns={'raceId': 'wins'})
    top_15_driver_nat = driver_nat.nlargest(15, 'wins')
    fig_driver_nat_bar = px.bar(
        top_15_driver_nat.sort_values('wins', ascending=True),
        x='wins', y='nationality_driver', orientation='h',
        title='Top 15 Wins by Driver Nationality',
        template=plotly_template
    )
    fig_driver_nat_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, xaxis_title="Total Wins", yaxis_title="Nationality")
    fig_driver_nat_bar.update_traces(marker_color='#00D2BE')

    # --- Driver Poles Bar ---
    driver_poles = poles_dff.groupby('driver_name')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_driver_poles = px.bar(driver_poles.sort_values('raceId', ascending=True), x='raceId', y='driver_name', orientation='h', title="Most Pole Positions by Driver", template=plotly_template)
    fig_driver_poles.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Driver", xaxis_title="Number of Poles")
    fig_driver_poles.update_traces(marker_color='#007BFF')
    
    # --- Constructor Poles Bar ---
    constructor_poles = poles_dff.groupby('name_constructor')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_constructor_poles = px.bar(constructor_poles.sort_values('raceId', ascending=True), x='raceId', y='name_constructor', orientation='h', title="Most Pole Positions by Constructor", template=plotly_template)
    fig_constructor_poles.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Constructor", xaxis_title="Number of Poles")
    fig_constructor_poles.update_traces(marker_color='#007BFF')

    # --- Driver Wins Bar ---
    driver_wins = winners_dff.groupby('driver_name')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_driver_wins = px.bar(driver_wins.sort_values('raceId', ascending=True), x='raceId', y='driver_name', orientation='h', title="Most Races Won by Driver", template=plotly_template)
    fig_driver_wins.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Driver", xaxis_title="Number of Wins")
    fig_driver_wins.update_traces(marker_color='#E10600')

    # --- Driver Podiums Bar ---
    driver_podiums = podiums_dff.groupby('driver_name')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_podiums = px.bar(driver_podiums.sort_values('raceId', ascending=True), x='raceId', y='driver_name', orientation='h', title="Most Podiums by Driver", template=plotly_template)
    fig_podiums.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Driver", xaxis_title="Number of Podiums")
    fig_podiums.update_traces(marker_color='#00D2BE')

    # --- Constructor Wins Bar ---
    constructor_wins = winners_dff.groupby('name_constructor')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_constructor_wins = px.bar(constructor_wins.sort_values('raceId', ascending=True), x='raceId', y='name_constructor', orientation='h', title="Most Races Won by Constructor", template=plotly_template)
    fig_constructor_wins.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Constructor", xaxis_title="Number of Wins")
    fig_constructor_wins.update_traces(marker_color='#E10600')

    # --- Constructor Podiums Bar ---
    constructor_podiums = podiums_dff.groupby('name_constructor')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_constructor_podiums = px.bar(constructor_podiums.sort_values('raceId', ascending=True), x='raceId', y='name_constructor', orientation='h', title="Most Podiums by Constructor", template=plotly_template)
    fig_constructor_podiums.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Constructor", xaxis_title="Number of Podiums")
    fig_constructor_podiums.update_traces(marker_color='#00D2BE')

    # --- Top Circuits Bar ---
    top_circuits = dff.groupby('name_circuit')['raceId'].nunique().reset_index().nlargest(15, 'raceId')
    fig_top_circuits = px.bar(top_circuits.sort_values('raceId', ascending=True), x='raceId', y='name_circuit', orientation='h', title="Most Races Hosted by Circuit", template=plotly_template)
    fig_top_circuits.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Circuit Name", xaxis_title="Number of Races")
    fig_top_circuits.update_traces(marker_color='#007BFF') 


    # --- Return all figures ---
    return (
        kpi_races_val, kpi_drivers_val, kpi_constructors_val,
        year_range_text, # NEW
        fig_races_season, fig_races_country, fig_pie_constructor_nat, fig_driver_nat_bar,
        fig_driver_poles, fig_constructor_poles, 
        fig_driver_wins, fig_podiums,
        fig_constructor_wins, fig_constructor_podiums, 
        fig_top_circuits
    )


# --- Driver Tab Callbacks ---
@app.callback(
    Output('driver-wins-over-time-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('driver-dropdown', 'value')]
)
def update_driver_line_chart(year_range, selected_drivers):
    if not selected_drivers:
        return create_empty_figure("Please select a driver from the dropdown.")
    
    dff = winners[
        (winners['year'] >= year_range[0]) & 
        (winners['year'] <= year_range[1]) &
        (winners['driver_name'].isin(selected_drivers))
    ]
    
    if dff.empty:
        return create_empty_figure("No wins for selected driver(s) in this period.")
    
    driver_wins_time = dff.groupby(['year', 'driver_name'])['raceId'].count().reset_index()
    driver_wins_time = driver_wins_time.rename(columns={'raceId': 'wins'})
    driver_wins_time['cumulative_wins'] = driver_wins_time.groupby('driver_name')['wins'].cumsum()

    fig = px.line(
        driver_wins_time, x='year', y='cumulative_wins', color='driver_name',
        title='Cumulative Wins Over Time for Selected Drivers',
        template=plotly_template, markers=True
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Cumulative Wins")
    return fig

@app.callback(
    Output('driver-points-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('driver-dropdown', 'value')]
)
def update_driver_points_chart(year_range, selected_drivers):
    if not selected_drivers:
        return create_empty_figure("Please select a driver from the dropdown.")

    dff = driver_points[
        (driver_points['year'] >= year_range[0]) & 
        (driver_points['year'] <= year_range[1]) &
        (driver_points['driver_name'].isin(selected_drivers))
    ]

    if dff.empty:
        return create_empty_figure("No points for selected driver(s) in this period.")

    fig = px.line(
        dff, x='year', y='points', color='driver_name',
        title='Points per Season for Selected Drivers',
        template=plotly_template, markers=True
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Seasonal Points")
    return fig


# --- Constructor Tab Callbacks ---
@app.callback(
    Output('constructor-wins-over-time-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('constructor-dropdown', 'value')]
)
def update_constructor_line_chart(year_range, selected_constructors):
    if not selected_constructors:
        return create_empty_figure("Please select a constructor from the dropdown.")

    dff = winners[
        (winners['year'] >= year_range[0]) & 
        (winners['year'] <= year_range[1]) &
        (winners['name_constructor'].isin(selected_constructors))
    ]
    
    if dff.empty:
        return create_empty_figure("No wins for selected constructor(s) in this period.")
    
    constructor_wins_time = dff.groupby(['year', 'name_constructor'])['raceId'].count().reset_index()
    constructor_wins_time = constructor_wins_time.rename(columns={'raceId': 'wins'})
    constructor_wins_time['cumulative_wins'] = constructor_wins_time.groupby('name_constructor')['wins'].cumsum()

    fig = px.line(
        constructor_wins_time, x='year', y='cumulative_wins', color='name_constructor',
        title='Cumulative Wins Over Time for Selected Constructors',
        template=plotly_template, markers=True
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Cumulative Wins")
    return fig

@app.callback(
    Output('constructor-points-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('constructor-dropdown', 'value')]
)
def update_constructor_points_chart(year_range, selected_constructors):
    if not selected_constructors:
        return create_empty_figure("Please select a constructor from the dropdown.")

    dff = constructor_points[
        (constructor_points['year'] >= year_range[0]) & 
        (constructor_points['year'] <= year_range[1]) &
        (constructor_points['name_constructor'].isin(selected_constructors))
    ]

    if dff.empty:
        return create_empty_figure("No points for selected constructor(s) in this period.")

    fig = px.line(
        dff, x='year', y='points', color='name_constructor',
        title='Points per Season for Selected Constructors',
        template=plotly_template, markers=True
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Seasonal Points")
    return fig


# --- Circuit Tab Callbacks ---
@app.callback(
    Output('circuit-races-over-time-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('circuit-dropdown', 'value')] 
)
def update_circuit_winners_chart(year_range, selected_circuit):
    if not selected_circuit:
        return create_empty_figure("Please select a circuit from the dropdown.")

    dff = winners[
        (winners['year'] >= year_range[0]) & 
        (winners['year'] <= year_range[1]) &
        (winners['name_circuit'] == selected_circuit)
    ]
    
    if dff.empty:
        return create_empty_figure("No winners at this circuit in this period.")
        
    circuit_winners = dff.groupby('driver_name')['raceId'].nunique().reset_index()
    circuit_winners = circuit_winners.rename(columns={'raceId': 'Wins'})
    top_10_winners = circuit_winners.nlargest(10, 'Wins')

    fig = px.bar(
        top_10_winners.sort_values('Wins', ascending=True), 
        x='Wins', y='driver_name', orientation='h',
        title=f"Top 10 Drivers by Wins at {selected_circuit}",
        template=plotly_template
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, xaxis_title="Total Wins", yaxis_title="Driver")
    fig.update_traces(marker_color='#007BFF')
    return fig

@app.callback(
    Output('constructor-wins-at-circuit-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('circuit-dropdown', 'value')] 
)
def update_circuit_constructor_winners_chart(year_range, selected_circuit):
    if not selected_circuit:
        return create_empty_figure("Please select a circuit from the dropdown.")

    dff = winners[
        (winners['year'] >= year_range[0]) & 
        (winners['year'] <= year_range[1]) &
        (winners['name_circuit'] == selected_circuit)
    ]
    
    if dff.empty:
        return create_empty_figure("No winners at this circuit in this period.")
        
    circuit_winners = dff.groupby('name_constructor')['raceId'].nunique().reset_index()
    circuit_winners = circuit_winners.rename(columns={'raceId': 'Wins'})
    top_10_winners = circuit_winners.nlargest(10, 'Wins')

    fig = px.bar(
        top_10_winners.sort_values('Wins', ascending=True), 
        x='Wins', y='name_constructor', orientation='h',
        title=f"Top 10 Constructors by Wins at {selected_circuit}",
        template=plotly_template
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, xaxis_title="Total Wins", yaxis_title="Constructor")
    fig.update_traces(marker_color='#E10600') # F1 Red
    return fig

@app.callback(
    Output('driver-poles-at-circuit-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('circuit-dropdown', 'value')] 
)
def update_circuit_poles_chart(year_range, selected_circuit):
    if not selected_circuit:
        return create_empty_figure("Please select a circuit from the dropdown.")

    dff = poles[
        (poles['year'] >= year_range[0]) & 
        (poles['year'] <= year_range[1]) &
        (poles['name_circuit'] == selected_circuit)
    ]
    
    if dff.empty:
        return create_empty_figure("No pole positions at this circuit in this period.")
        
    circuit_poles = dff.groupby('driver_name')['raceId'].nunique().reset_index()
    circuit_poles = circuit_poles.rename(columns={'raceId': 'Poles'})
    top_10_poles = circuit_poles.nlargest(10, 'Poles')

    fig = px.bar(
        top_10_poles.sort_values('Poles', ascending=True), 
        x='Poles', y='driver_name', orientation='h',
        title=f"Top 10 Drivers by Poles at {selected_circuit}",
        template=plotly_template
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, xaxis_title="Total Pole Positions", yaxis_title="Driver")
    fig.update_traces(marker_color='#00D2BE') # Podium Teal
    return fig

# ==============================================================================
#  6. RUN THE APP
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True)