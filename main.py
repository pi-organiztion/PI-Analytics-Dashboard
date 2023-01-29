"""Generates the analytics dashboard to a local host using the given tasks data."""

import pandas as pd
import pyodbc
import json
from dash import Dash, Input, Output
from modules import preprocessing, wc_analytics, driver_analytics, layouts

# Load in the SQL Config
sql_config_fp = './configs/sql_config.json'
with open(sql_config_fp, 'r') as file:
  sql_config = json.load(file)

# Point to the SQL server and make a SQL querry for the tasks dataset
cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='
                      + sql_config['server']
                      + ';DATABASE='
                      + sql_config['database']
                      + ';UID='
                      + sql_config['user']
                      + ';PWD='
                      + sql_config['pass'])
cursor = cnxn.cursor()

query = """
SELECT t.TaskId             AS [Task #],
       u.UserName           AS Driver,
       f.ForkliftName       AS Forklift,
       w.WorkcenterCode     AS Workcenter,
       t.PartNo             AS [Part No],
       CASE t.Status
          WHEN 1 THEN 'Waiting'
          WHEN 2 THEN 'In-Progress'
          ELSE 'Completed'
       END                  AS Status,
       CASE t.taskType
          WHEN 1 THEN 'F/G Put Away'
          WHEN 2 THEN 'Replenishment'
          WHEN 3 THEN 'Part Return'
          WHEN 4 THEN 'FG Return'
          WHEN 5 THEN 'Container Move'
          ELSE ''
       END                  AS Name, 
       t.CreationTime       AS [Creation Time],
       t.StartTime          AS [Start Time],
       t.EndTime            AS [End Time],
       t.Distance
FROM Task t
     INNER JOIN [User] u
             ON t.AssignUserId = u.UserId
     INNER JOIN Workcenter w
             ON t.WorkcenterKey = w.WorkcenterKey
     LEFT JOIN Forklift f
            ON t.TagId = f.TagId
"""

# Execute SQL querry and preprocess the tasks dataset
tasks = pd.read_sql(query, cnxn)
tasks = preprocessing.preprocess_task_data(tasks)

# Load in Markdown File
md_filepath = './assets/reading_guide_md.txt'
with open(md_filepath, encoding = 'utf-8') as f:
  reading_guide_md = f.read()

# PI's Dashboard Color Gradient
pi_colorscale = ['#B4BDD0', '#8593B2', '#5B6E98',
                 '#2D457B', '#082464', '#141C5C',
                 '#211555', '#2E0E4E', '#3A0647',
                 '#340341']

# Preset Colors
task_type_colors = {'F/G Put Away': '#60386C',
                    'Replenishment': '#C4B5C8',
                    'Container Move': '#9A5EAC'}
driver_colors = driver_analytics.assign_driver_colors(tasks)

# Collect Key Values
latest_date = tasks['Creation Time'].iloc[0].replace(hour=0, minute=0, second=0, microsecond=0)
end_dates = {'Full History': pd.to_datetime('2000-01-01', format='%Y-%m-%d'),
             'Past 365-Days': latest_date - pd.Timedelta(365, unit='D'),
             'Past 90-Days': latest_date - pd.Timedelta(90, unit='D'),
             'Past 60-Days': latest_date - pd.Timedelta(60, unit='D'),
             'Past 30-Days': latest_date - pd.Timedelta(30, unit='D')}
rollover_periods = {'2-Hours': 7200,  # Time in seconds
                    '1.5-Hours': 5400,
                    '1-Hour': 3600,               
                    '30-Mins': 1800,
                    '15-Mins': 900}     
stat_block_values = wc_analytics.generate_stat_block_values(tasks)

# Create the Analytics Dashboard HTML and CSS Layout
external_stylesheets = ['https://fonts.googleapis.com/css2?family=Roboto&display=swap']
app = Dash(__name__,
           assets_folder='./assets/',
           meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
           external_stylesheets=external_stylesheets,
           update_title='Loading...')
app.layout = layouts.create_app_layout(stat_block_values, reading_guide_md)
server = app.server


# Tab Selection Dash Functions
@app.callback(Output('analytics-type', 'children'),
              Input('tab-selection', 'value'))
def show_current_tab_text(current_tab_selection):
  overview_tabs = {'Work Centers': 'Work Center Overview',
                   'Drivers': 'Drivers Overview'}
  return overview_tabs[current_tab_selection]


# Work Center Tab Dash Functions
@app.callback(Output('wc-efficiency-table-name', 'children'),
              Input('wc-lookback-period', 'value'))
def get_wc_efficiency_table_name(lookback_period):
  return f'Work Center Efficiency Ratios ({lookback_period})'

@app.callback(Output('wc-task-bars', 'figure'),
              Input('split-by-types', 'value'),
              Input('wc-range-tasks', 'value'),
              Input('wc-lookback-period', 'value'))
def show_wc_task_bars(split_by_types, wc_range, lookback_period):
  end_date = end_dates[lookback_period]
  split = True if split_by_types == 'Yes' else False

  if split:
    fig = wc_analytics.create_task_type_bars(tasks,
                                             wc_range,
                                             end_date,
                                             lookback_period,
                                             task_type_colors)
  else:
    fig = wc_analytics.create_task_bars(tasks,
                                        wc_range,
                                        end_date,
                                        lookback_period,
                                        pi_colorscale)
  return fig

@app.callback(Output('wc-queue-bars', 'figure'),
              Input('rollover-period', 'value'),
              Input('wc-range-queue', 'value'),
              Input('wc-lookback-period', 'value'))
def show_wc_queue_bars(rollover_period, wc_range, lookback_period):
  end_date = end_dates[lookback_period]
  rollover_period = rollover_periods[rollover_period] if rollover_period != 'No' else False

  if rollover_period:
    fig = wc_analytics.create_rollover_queue_bars(tasks,
                                                  rollover_period,
                                                  wc_range, 
                                                  end_date,
                                                  lookback_period,
                                                  pi_colorscale) 
  else:
    fig = wc_analytics.create_queue_bars(tasks,
                                         wc_range,
                                         end_date,
                                         lookback_period,
                                         pi_colorscale)
  return fig

@app.callback(Output('wc-task-type-pi', 'figure'),
              Input('wc-lookback-period', 'value'))
def show_wc_task_type_pi(lookback_period):
  end_date = end_dates[lookback_period]
  fig = wc_analytics.create_task_type_pi(tasks,
                                         end_date,
                                         lookback_period,
                                         task_type_colors)
  return fig

@app.callback(Output('wc-task-select', 'options'),
              Output('wc-task-select', 'value'),
              Input('wc-lookback-period', 'value'))
def show_top_10_tasks(lookback_period):
  end_date = end_dates[lookback_period]
  options, value = wc_analytics.get_top_10_tasks_dropdown(tasks, end_date)
  return options, value

@app.callback(Output('task-times-distrib', 'figure'),
              Input('wc-task-select', 'value'),
              Input('wc-lookback-period', 'value'))
def show_task_time_distrib(task_info, lookback_period):
  end_date = end_dates[lookback_period]
  fig = wc_analytics.create_task_time_distrib(tasks, task_info, end_date)
  return fig

@app.callback(Output('wc-efficiency-table', 'data'),
              Output('wc-efficiency-table', 'columns'),
              Input('wc-lookback-period', 'value'))
def show_wc_efficiency_table(lookback_period):
  end_date = end_dates[lookback_period]
  table_df = wc_analytics.create_efficiency_table(tasks, end_date)
  return table_df.to_dict('records'), [{'name': i, 'id': i} for i in table_df.columns]


# Driver Tab Dash Functions
@app.callback(Output('driver-efficiency-table-name', 'children'),
              Input('driver-lookback-period', 'value'))
def get_driver_efficiency_table_name(lookback_period):
  return f'Driver Efficiency Ratios ({lookback_period})'

@app.callback(Output('driver-task-hist-lines', 'figure'),
              Input('driver-lookback-period', 'value'))
def show_driver_task_lines(lookback_period):
  end_date = end_dates[lookback_period]
  fig = driver_analytics.create_task_lines(tasks,
                                           end_date,
                                           lookback_period,
                                           driver_colors)
  return fig

@app.callback(Output('driver-task-select', 'options'),
              Output('driver-task-select', 'value'),
              Input('driver-lookback-period', 'value'))
def show_top_10_tasks(lookback_period):
  end_date = end_dates[lookback_period]
  options, value = driver_analytics.get_top_10_tasks_dropdown(tasks, end_date)
  return options, value

@app.callback(Output('driver-dur-bars', 'figure'), 
              Input('driver-task-select', 'value'),       
              Input('driver-lookback-period', 'value'))
def show_driver_dur_bars(task_info, lookback_period):
  end_date = end_dates[lookback_period]
  fig = driver_analytics.create_dur_bars(tasks,
                                          task_info,
                                          end_date,
                                          lookback_period,
                                          driver_colors)
  return fig

@app.callback(Output('driver-dur-dist-bars', 'figure'), 
              Input('driver-task-select', 'value'),       
              Input('driver-lookback-period', 'value'))
def show_driver_dist_bars(task_info, lookback_period):
  end_date = end_dates[lookback_period]
  fig = driver_analytics.create_dur_dist_bars(tasks,
                                              task_info,
                                              end_date,
                                              lookback_period,
                                              driver_colors)
  return fig


@app.callback(Output('driver-efficiency-table', 'data'),
              Output('driver-efficiency-table', 'columns'),
              Input('driver-lookback-period', 'value'))
def show_driver_efficiency_table(lookback_period):
  end_date = end_dates[lookback_period]
  table_df = driver_analytics.create_efficiency_table(tasks, end_date)
  return table_df.to_dict('records'), [{'name': i, 'id': i} for i in table_df.columns]

@app.callback(Output('driver-task-perc-pi', 'figure'),
              Input('driver-lookback-period', 'value'))
def show_driver_task_pi(lookback_period):
  end_date = end_dates[lookback_period]
  fig = driver_analytics.create_task_pi(tasks,
                                        end_date,
                                        lookback_period,
                                        driver_colors)
  return fig


# Reading Guide Dash Functions
@app.callback(Output('wc-rg-popup', 'style'),
              Input('wc-rg-open-button', 'n_clicks'))
def show_wc_reading_guide(n_clicks_open):
  if n_clicks_open > 0:
    return {"display": "block"}
  return {"display": "none"}

@app.callback(Output('wc-rg-open-button', 'n_clicks'),
              Input('wc-rg-close-button', 'n_clicks'))
def close_wc_reading_guide(n_clicks_close):
  return 0

@app.callback(Output('driver-rg-popup', 'style'),
              Input('driver-rg-open-button', 'n_clicks'))
def show_driver_reading_guide(n_clicks_open):
  if n_clicks_open > 0:
    return {"display": "block"}
  return {"display": "none"}

@app.callback(Output('driver-rg-open-button', 'n_clicks'),
              Input('driver-rg-close-button', 'n_clicks'))
def close_driver_reading_guide(n_clicks_close):
  return 0


# Run Dash Application
if __name__ == "__main__":
  app.run_server(debug=False)
