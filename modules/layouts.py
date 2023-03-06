"""Generates the HTML Structure for the Analytics Dashboard Layout using Dash.

Functions:
  create_app_layout(stat_block_values, reading_guide_md):
    Creates the HTML structure of the analytics dashboard application layout.

  create_stat_block_header():
    Creates the HTML structure of the header and its stat blocks.
  
  create_wc_tab():
    Creates the HTML structure of the Work Center Tab.

  create_driver_tab():
    Creates the HTML structure of the Driver Tab.

  create_rg_popup(reading_guide_md, tab):
    Creates the HTML structure of the reading guide popup.
"""

from dash import dcc, html, dash_table

def create_app_layout(appsettings_config,stat_block_values, reading_guide_md):
  """Creates the HTML structure of the analytics dashboard application layout.
  
  Args:
    appsettings_config: Values in configs/appsettings.json
    stat_block_values: A list of stat block values to display in the header.
    reading_guide_md: A string markdown that describes how to use and read 
                      the analytics dashboard.

  Returns:
    app_layout: A dash.html.Div object that details the structure of the
                analytics dashboard. This dash.html.Div object will get assigned
                app.layout.
  """

  app_layout = html.Div(
    [create_stat_block_header(appsettings_config,stat_block_values),
    html.Hr(className='main-break-line'),

    dcc.Tabs(className='tabs',
             id='tab-selection',
             value='Work Centers',
             colors={'border':'white',
                     'primary': '#F9FAFB', 
                     'background': '#DADBDC'},
             children=[create_wc_tab(), create_driver_tab()]),
    
    create_rg_popup(reading_guide_md, tab='wc'),
    create_rg_popup(reading_guide_md, tab='driver')
    ]
  )
  return app_layout

def create_stat_block_header(appsettings_config,stat_block_values):
  """Creates the HTML structure of the header and its stat blocks.
  
  Args:
    appsettings_config: Values in configs/appsettings.json
    stat_block_values: A list of stat block values to display in the header.

  Returns:
    stat_block_header: A dash.html.Div object that details the structure of the
                       stat block header 
  """

  stat_block_header = (
    html.Div(className='header-row', children=[
        html.H1(["Smart Warehouse", html.Br(), html.Span(id='analytics-type')]),
        html.Div(className='stats', children=[
          html.Div(className='stat-block', id='stat-block-1', children=[
            html.Span(f"{stat_block_values[0]}"), html.Br(), "Tasks Completed Today"]),                                      
          html.Div(className='stat-block', id='stat-block-2', children=[
            html.Span(f"{stat_block_values[1]}"), html.Br(), "Tasks Currently Queued"]),
          html.Div(className='stat-block', id='stat-block-3', children=[
            html.Span(f"{stat_block_values[2]}"), html.Br(), "Monthly Tasks Completed"]),               
          html.Div(className='stat-block', id='stat-block-4', children=[
            html.Span(f"{stat_block_values[3]}"), html.Br(), "Average Tasks Completed", html.Br(), "(per day)"]),       
          html.Div(className='stat-block', id='stat-block-5', children=[
            html.Span(f"{stat_block_values[4]}"), html.Br(), "Average Tasks Completed", html.Br(), "(per month)"])
        ])       
    ])
  )
  if appsettings_config.get('realTimeDataAPPURL') is not None:
    stat_block_header.children.append(html.A('Real Time Data',href=appsettings_config['realTimeDataAPPURL'], className='right real-time-data'))
  else:
    stat_block_header.children.append(html.Div(className='right'))
  return stat_block_header

def create_wc_tab():
  """Creates the HTML structure of the Work Center Tab.

  Returns:
    wc_tab: A dash.dcc.Tab object that details the HTML 
            structure of the selected work center tab
  """

  wc_tab = (
    dcc.Tab(className='tab',
            selected_style={'background-color': '#F9FAFB'},
            label='Work Centers',
            value='Work Centers',
            children=[
      html.Div(className='wc-grid-container', children=[

        html.Div(className='wc-task', children=[
          dcc.Graph(id='wc-task-bars',
                    style={'height': '68%'},
                    config={'responsive':True},
                    responsive=True),                       
          html.Hr(className='dropdown-break-line'),
          html.Div(children=[
            html.P('Work Centers Selection:', style={'margin-left': '4.75%', 'margin-bottom': '2%'}),
            dcc.RangeSlider(className='wc-range-slider',
                            id='wc-range-tasks',                              
                            min=1, max=17, step=3, value=[1, 17],
                            tooltip={"placement": "bottom", "always_visible": True})
          ]),                                            
          html.Div(className='option-bar', children=[
            html.P('Show Task Types:', style={'display': 'inline-block', 'margin-left':'-0.25%', 'margin-top': '2%'}),
            dcc.Dropdown(id='split-by-types',
                         className='dropdown',
                         options=['Yes', 'No'],
                         value='No',
                         style={'display': 'inline-block', 
                                'verticalAlign': 'middle',
                                'margin-left': '2%',
                                'width': '50%'},
                         searchable=False,
                         clearable=False)
          ])
        ]),

        html.Div(className='wc-task-type', children=[
          dcc.Graph(id='wc-task-type-pi', 
                    style={'height': '100%'},
                    config={'responsive': True},
                    responsive=True)
        ]),

        html.Div(className='task-times', children=[
            dcc.Graph(id='task-times-distrib',
                      style={'height': '75%'},
                      config={'responsive':True},
                      responsive=True),
            html.Hr(className='dropdown-break-line'),
            html.Div(className='option-bar', children=[
              html.P('Select Task Name:', style={'display': 'inline-block'}),
              dcc.Dropdown(id='wc-task-select',
                           className='dropdown',
                           style={'display': 'inline-block', 
                                  'verticalAlign': 'middle',
                                  'width': '75%',
                                  'margin-left': '2%'})
            ])
          ]),  

        html.Div(className='wc-queue', children=[
          dcc.Graph(id='wc-queue-bars',
                    style={'height': '70%'},
                    config={'responsive': True},
                    responsive=True),
          html.Hr(className='dropdown-break-line'),
          html.Div(children=[
            html.P('Work Centers Selection:', style={'margin-left': '4.75%', 'margin-bottom': '2%'}),
            dcc.RangeSlider(className='wc-range-slider',
                            id='wc-range-queue',                              
                            min=1, max=17, step=3, value=[1, 17],
                            tooltip={"placement": "bottom", "always_visible": True})
          ]),   
          html.Div(className='option-bar', children=[                  
            html.P('Count Task Rollover?', style={'display': 'inline-block', 'margin-left':'-0.25%'}),
            dcc.Dropdown(id='rollover-period',                  
                         options=['2-Hours', '1.5-Hours', '1-Hour', '30-Mins', '15-Mins', 'No'],
                         value='No',
                         style={'display': 'inline-block', 
                                'verticalAlign': 'middle',
                                'margin-left': '2%',
                                'width': '50%'},
                         searchable=False,
                         clearable=False)
          ])
        ]),
                            
        html.Div(className='wc-efficiency', children=[
          html.P(id='wc-efficiency-table-name', style={'margin-left': '0.5%'}),
          dash_table.DataTable(id='wc-efficiency-table',
                               sort_action='native',
                               style_table={'height': '500px',
                                            'maxHeight': '550px',
                                            'overflowY': 'auto'},
                               style_data={'width': '60px',
                                           'max-width': '60px',
                                           'min-width': '60px',
                                           'height': 'auto'},                                
                               fixed_rows={'headers': True})
        ]),

        html.Div(className='wc-overview-options', children=[
          html.Button('Reading Guide',                                                        
                      className='overview-option',
                      id='wc-rg-open-button',
                      style={'padding': '2% 1% 2% 1%'}),
          html.Button('Reports',
                      className='overview-option',
                      id='wc-report-button',
                      style={'padding': '2% 1% 2% 1%'}),
          html.Div(className='overview-option',
                   style={'width': '42%'},        
                   children=[
                    html.P('Timeframe Selection:',
                           style={'display': 'inline-block',
                                  'padding-left': '1%',
                                  'verticalAlign': 'middle'}),
                    html.Div(style={'margin-left': '2%',
                                    'width': '51%',
                                    'display': 'inline-block',
                                    'verticalAlign': 'middle'},                    
                             children=dcc.Dropdown(id='wc-lookback-period',
                                                   value='Full History',
                                                   searchable=False,
                                                   clearable=False,
                                                   style={'color': 'black'},
                                                   options=[{'label': "View Full History", 'value': "Full History"},
                                                            {'label': 'View Past 365-Days', 'value': 'Past 365-Days'},
                                                            {'label': "View Past 90-Days", 'value': "Past 90-Days"},
                                                            {'label': "View Past 60-Days", 'value': "Past 60-Days"},
                                                            {'label': "View Past 30-Days", 'value': "Past 30-Days"}]))
          ])
        ])
      ])
    ])
  )
  return wc_tab

def create_driver_tab():
  """Creates the HTML structure of the Driver Tab.

  Returns:
    driver_tab: A dash.dcc.Tab object that details the HTML 
                structure of the selected driver tab.
  """

  driver_tab = (
    dcc.Tab(className='tab',
            label='Drivers',
            value='Drivers',
            selected_style={'background-color': '#F9FAFB'},
            children=[
      html.Div(className='driver-grid-container', children=[
        
        html.Div(className='driver-task-hist', children=[
          dcc.Graph(id='driver-task-hist-lines',
                    style={'height': '100%'},
                    config={'responsive': True},
                    responsive=True)
        ]),

        html.Div(className='driver-task-perc', children=[
          dcc.Graph(id='driver-task-perc-pi',
                    style={'height': '100%'},
                    config={'responsive': True},
                    responsive=True)
        ]),

        html.Div(className='driver-dur-dist', children=[
          dcc.Graph(id='driver-dur-dist-bars',
                    style={'height': '84%',
                           'width': '100%'},
                    config={'responsive': True},
                    responsive=True),
          html.Hr(className='dropdown-break-line'),
          html.Div(className='option-bar', children=[
            html.P('Select Task Name:', style={'display': 'inline-block'}),
            dcc.Dropdown(id='driver-task-select',
                         className='dropdown',
                         style={'display': 'inline-block', 
                                'verticalAlign': 'middle',
                                'width': '65%',
                                'margin-left': '2%'})
          ])
        ]),

        html.Div(className='driver-efficiency', children=[
          html.P(id='driver-efficiency-table-name', style={'margin-left': '0.5%'}),
          dash_table.DataTable(id='driver-efficiency-table',                              
                               sort_action='native',
                               style_table={'height': '400px',
                                            'maxHeight': '450px',
                                            'overflowY': 'auto'},
                               page_count=5,
                               page_size=5)
        ]),
              
        html.Div(className='driver-overview-options', children=[
          html.Button('Reading Guide',                                                        
                      className='overview-option',
                      id='driver-rg-open-button',
                      style={'padding': '2% 1% 2% 1%'}),
          html.Button('Reports',
                      className='overview-option',
                      id='driver-report-button',
                      style={'padding': '2% 1% 2% 1%'}),
          html.Div(className='overview-option',
                   style={'width': '59%'},        
                   children=[
                    html.P('Timeframe Selection:',
                            style={'display': 'inline-block',
                                   'padding-left': '1%',
                                   'verticalAlign': 'middle'}),
                    html.Div(style={'margin-left': '2%',
                                    'width': '51%',
                                    'display': 'inline-block',
                                    'verticalAlign': 'middle'},                    
                             children=dcc.Dropdown(id='driver-lookback-period',
                                                   value="Full History",
                                                   searchable=False,
                                                   clearable=False,
                                                   style={'color': 'black'},
                                                   options=[{'label': "View Full History", 'value': "Full History"},
                                                            {'label': "View Past 365-Days", 'value': "Past 365-Days"},
                                                            {'label': "View Past 90-Days", 'value': "Past 90-Days"},
                                                            {'label': "View Past 60-Days", 'value': "Past 60-Days"},
                                                            {'label': "View Past 30-Days", 'value': "Past 30-Days"}]))
            ])
        ])
      ])
    ])
  )
  return driver_tab

def create_rg_popup(reading_guide_md, tab='wc'):
  """Creates the HTML structure of the reading guide popup.
  
  Args:
    reading_guide_md: A string markdown that describes how to use and read 
                      the analytics dashboard.
    tab: A string that denotes which tab the reading guide popup
         belongs to. Options are {'wc', 'driver'}. Defaults 'wc'.
         The tab value denotes the id of the HTML div cell. The ids'
         must be unique for each tab.
  
  Returns:
    reading_guide_popup: A dash.html.Div object that details the HTML 
                structure of the reading guide popup.
  """

  reading_guide_popup = (
    html.Div(className='modal',
             id=f'{tab}-rg-popup',
             style={"display": "none"},
             children=[
              html.Div(className='rg-content',
                       children=[
                        dcc.Markdown(reading_guide_md),
                        html.Button('Close',
                                    style={'padding': '0.5% 0.5% 0.5% 0.5%'},
                                    className='overview-option',
                                    id=f'{tab}-rg-close-button')
              ])
    ])
  )
  return reading_guide_popup