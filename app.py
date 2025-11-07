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
#  1. DATA LOADING & PREPARATION (Your code is correct)
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

    # --- MODIFIED ---
    # Need to select the constructor nationality for the pie chart
    winners = df[df['position'] == 1]
    
    podiums = df[df['position'].isin([1, 2, 3])]
    constructor_points = df.groupby(['year', 'name_constructor'])['points'].sum().reset_index()
    
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
    df = pd.DataFrame(columns=['year', 'driver_name', 'name_constructor', 'points', 'position', 'name_race', 'country', 'driverId', 'constructorId', 'name_circuit', 'nationality_driver', 'nationality_constructor'])
    winners = pd.DataFrame(columns=['year', 'driver_name', 'name_constructor', 'nationality_driver', 'nationality_constructor']) # Added
    podiums = pd.DataFrame(columns=['year', 'driver_name', 'position'])
    constructor_points = pd.DataFrame(columns=['year', 'name_constructor', 'points'])
    min_year, max_year = 1950, 2024
    all_drivers, all_constructors, all_circuits = [], [], []

# ==============================================================================
#  2. APP INITIALIZATION (This is the correct, robust code)
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
#  4. APP LAYOUT (Logo link is fixed)
# ==============================================================================
app.layout = dbc.Container(
    [
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
        
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H5("Filter by Year"),
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
        
        dcc.Tabs(
            id="dashboard-tabs",
            value="tab-overview",
            className="Tabs",
            children=[
                dcc.Tab(
                    label="Overview",
                    value="tab-overview",
                    className="Tab",
                    selected_className="Tab--selected",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(create_kpi_card("Total Races", 0, 'kpi-races'), md=4),
                                dbc.Col(create_kpi_card("Total Drivers", 0, 'kpi-drivers'), md=4),
                                dbc.Col(create_kpi_card("Total Constructors", 0, 'kpi-constructors'), md=4),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Races Per Season"),
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
                                            dcc.Graph(id='races-by-country-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        
                        # --- NEWLY ADDED ROW FOR PIE AND TREEMAP ---
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Winning Constructors by Nationality"),
                                            dcc.Graph(id='constructor-nat-pie') # New Graph ID
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            # --- TITLE CHANGED ---
                                            html.H5("Top 15 Wins by Driver Nationality"),
                                            dcc.Graph(id='driver-nat-treemap') # ID is the same
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                            ],
                            style={'margin-top': '20px'}
                        ),
                        # --- END OF NEWLY ADDED ROW ---
                    ]
                ),
                
                dcc.Tab(
                    label="Driver Analytics",
                    value="tab-drivers",
                    className="Tab",
                    selected_className="Tab--selected",
                    children=[
                        # ... (Rest of your tabs are unchanged) ...
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Driver Cumulative Wins Over Time"),
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
                                    md=12
                                )
                            ],
                            style={'margin-top': '20px'}
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Drivers by Wins (Selected Years)"),
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
                
                dcc.Tab(
                    label="Constructor Analytics",
                    value="tab-constructors",
                    className="Tab",
                    selected_className="Tab--selected",
                    children=[
                         dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Constructor Cumulative Wins Over Time"),
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
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Constructors by Wins (Selected Years)"),
                                            dcc.Graph(id='constructor-wins-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=12
                                )
                            ],
                            style={'margin-top': '20px'}
                        ),
                    ]
                ),

                # --- "CIRCUITS" TAB ---
                dcc.Tab(
                    label="Circuit Analytics",
                    value="tab-circuits",
                    className="Tab",
                    selected_className="Tab--selected",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5("Top 15 Circuits by Race Count (Selected Years)"),
                                            dcc.Graph(id='top-circuits-chart')
                                        ], 
                                        className="graph-container"
                                    ),
                                    md=6
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            # *** THIS IS THE CHANGE (Line 258) ***
                                            html.H5("Top 10 Winningest Drivers at Selected Circuit"),
                                            html.Label("Select a Circuit:"),
                                            dcc.Dropdown(
                                                id='circuit-dropdown',
                                                options=[{'label': c, 'value': c} for c in all_circuits],
                                                value='Autodromo Nazionale di Monza',
                                                multi=False, 
                                                className="Dropdown"
                                            ),
                                            # The ID 'circuit-races-over-time-chart' stays the same
                                            dcc.Graph(id='circuit-races-over-time-chart')
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

# --- MODIFIED CALLBACK (ADDED 2 NEW OUTPUTS) ---
@app.callback(
    [
        Output('kpi-races', 'children'),
        Output('kpi-drivers', 'children'),
        Output('kpi-constructors', 'children'),
        Output('races-per-season-chart', 'figure'),
        Output('races-by-country-chart', 'figure'),
        Output('driver-wins-chart', 'figure'),
        Output('constructor-wins-chart', 'figure'),
        Output('podiums-chart', 'figure'),
        Output('top-circuits-chart', 'figure'),
        Output('constructor-nat-pie', 'figure'), # --- NEWLY ADDED ---
        Output('driver-nat-treemap', 'figure'), # --- NEWLY ADDED ---
    ],
    [Input('year-slider', 'value')]
)
def update_overview_graphs(year_range):
    dff = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]
    winners_dff = winners[(winners['year'] >= year_range[0]) & (winners['year'] <= year_range[1])]
    podiums_dff = podiums[(podiums['year'] >= year_range[0]) & (podiums['year'] <= year_range[1])]

    kpi_races_val = f"{dff['raceId'].nunique():,}"
    kpi_drivers_val = f"{dff['driverId'].nunique():,}"
    kpi_constructors_val = f"{df['constructorId'].nunique():,}"

    races_per_season = dff.groupby('year')['raceId'].nunique().reset_index()
    fig_races_season = px.bar(races_per_season, x='year', y='raceId', title="Total Races Each Season", template=plotly_template)
    fig_races_season.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Number of Races")
    fig_races_season.update_traces(marker_color='#E10600')

    races_by_country = dff.groupby('country')['raceId'].nunique().reset_index().nlargest(15, 'raceId')
    fig_races_country = px.bar(races_by_country.sort_values('raceId', ascending=True), x='raceId', y='country', orientation='h', title="Top 15 Host Countries", template=plotly_template)
    fig_races_country.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Country", xaxis_title="Number of Races")
    fig_races_country.update_traces(marker_color='#E10600')

    driver_wins = winners_dff.groupby('driver_name')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_driver_wins = px.bar(driver_wins.sort_values('raceId', ascending=True), x='raceId', y='driver_name', orientation='h', title="Most Races Won by Driver", template=plotly_template)
    fig_driver_wins.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Driver", xaxis_title="Number of Wins")
    fig_driver_wins.update_traces(marker_color='#E10600')

    constructor_wins = winners_dff.groupby('name_constructor')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_constructor_wins = px.bar(constructor_wins.sort_values('raceId', ascending=True), x='raceId', y='name_constructor', orientation='h', title="Most Races Won by Constructor", template=plotly_template)
    fig_constructor_wins.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Constructor", xaxis_title="Number of Wins")
    fig_constructor_wins.update_traces(marker_color='#E10600')

    driver_podiums = podiums_dff.groupby('driver_name')['raceId'].count().reset_index().nlargest(15, 'raceId')
    fig_podiums = px.bar(driver_podiums.sort_values('raceId', ascending=True), x='raceId', y='driver_name', orientation='h', title="Most Podiums by Driver", template=plotly_template)
    fig_podiums.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Driver", xaxis_title="Number of Podiums")
    fig_podiums.update_traces(marker_color='#00D2BE')

    top_circuits = dff.groupby('name_circuit')['raceId'].nunique().reset_index().nlargest(15, 'raceId')
    fig_top_circuits = px.bar(top_circuits.sort_values('raceId', ascending=True), x='raceId', y='name_circuit', orientation='h', title="Most Races Hosted by Circuit", template=plotly_template)
    fig_top_circuits.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5, yaxis_title="Circuit Name", xaxis_title="Number of Races")
    fig_top_circuits.update_traces(marker_color='#007BFF') # Changed to F1 Yellow

    # --- MODIFIED: Pie Chart Logic ---
    constructor_nat = winners_dff.groupby('nationality_constructor')['raceId'].count().reset_index().rename(columns={'raceId': 'wins'})
    fig_pie_constructor_nat = px.pie(
        constructor_nat, 
        names='nationality_constructor', 
        values='wins', 
        title="Win % by Constructor Nationality",
        template=plotly_template,
        # This line adds the red color scale as requested
        color_discrete_sequence=px.colors.sequential.Reds 
    )
    fig_pie_constructor_nat.update_traces(textposition='inside', textinfo='percent+label', pull=[0.05] * len(constructor_nat))
    fig_pie_constructor_nat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        title_x=0.5,
        legend_title="Nationality"
    )
    # --- END OF MODIFICATION ---


    # --- MODIFIED: Treemap Logic changed to Bar Chart ---
    driver_nat = winners_dff.groupby('nationality_driver')['raceId'].count().reset_index().rename(columns={'raceId': 'wins'})
    
    # Get Top 15 nationalities
    top_15_driver_nat = driver_nat.nlargest(15, 'wins')

    # Create a horizontal bar chart
    fig_driver_nat_bar = px.bar(
        top_15_driver_nat.sort_values('wins', ascending=True), # Sort for horizontal bar
        x='wins',
        y='nationality_driver',
        orientation='h',
        title='Top 15 Wins by Driver Nationality', # Updated title
        template=plotly_template
    )
    fig_driver_nat_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        title_x=0.5,
        xaxis_title="Total Wins",
        yaxis_title="Nationality"
    )
    # Using the podium color for variety
    fig_driver_nat_bar.update_traces(marker_color='#00D2BE')
    # --- END OF MODIFICATION ---


    # --- MODIFIED RETURN STATEMENT (added new figs) ---
    return (kpi_races_val, kpi_drivers_val, kpi_constructors_val, fig_races_season, 
            fig_races_country, fig_driver_wins, fig_constructor_wins, fig_podiums,
            fig_top_circuits, fig_pie_constructor_nat, fig_driver_nat_bar) # Return the new bar chart


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
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5)
    return fig

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
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5)
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
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", title_x=0.5)
    return fig

# *** THIS IS THE CHANGED CALLBACK (Line 560) ***
@app.callback(
    # The Output ID is the same, so it just works
    Output('circuit-races-over-time-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('circuit-dropdown', 'value')] 
)
def update_circuit_winners_chart(year_range, selected_circuit): # Renamed function
    if not selected_circuit:
        return create_empty_figure("Please select a circuit from the dropdown.")

    # Use the 'winners' dataframe
    dff = winners[
        (winners['year'] >= year_range[0]) & 
        (winners['year'] <= year_range[1]) &
        (winners['name_circuit'] == selected_circuit)
    ]
    
    if dff.empty:
        return create_empty_figure("No winners at this circuit in this period.")
        
    # Group by driver, count wins, and get top 10
    circuit_winners = dff.groupby('driver_name')['raceId'].nunique().reset_index()
    circuit_winners = circuit_winners.rename(columns={'raceId': 'Wins'})
    top_10_winners = circuit_winners.nlargest(10, 'Wins')

    fig = px.bar(
        top_10_winners.sort_values('Wins', ascending=True), 
        x='Wins', 
        y='driver_name',
        orientation='h',
        title=f"Top Drivers at {selected_circuit}",
        template=plotly_template
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        title_x=0.5,
        xaxis_title="Total Wins",
        yaxis_title="Driver"
    )
    fig.update_traces(marker_color='#007BFF') # Changed to F1 Yellow
    return fig

# ==============================================================================
#  6. RUN THE APP
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True)