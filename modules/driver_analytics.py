"""Generates key values and graphs for the TED analytics dashboard tab.

Functions:
  assign_driver_colors(tasks):
    Assigns specific color codes to each driver (max 10 colors avaliable).

  create_task_lines(tasks,
                    end_date,
                    lookback_period,
                    driver_colors):
    Creates a line chart containing the total tasks completed by each driver each day.

  get_top_10_tasks_dropdown(tasks, end_date):
    Gets the top 10 most common tasks for the HTML dropdown selection.

  create_dur_dist_bars(tasks,
                         task_info,
                         end_date,
                         lookback_period,
                         driver_colors):
    Creates a bar graph containing the average duration and distance by each driver to complete the given task.

  _parse_task_info(task_info):
    Parses the given task information for its task name and its rank (rank 1 means it was the most common task).
  
  create_task_pi(tasks,
                 end_date,
                 lookback_period,
                 driver_colors):
    Creates a pi chart containing the total distribution of completed tasks by each driver.

  create_efficiency_table(tasks, end_date):
    Creates an efficiency table to display key statistics for each driver.
"""

import re
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def assign_driver_colors(tasks):
  """Assigns specific color codes to each driver (max 10 colors avaliable.

  px.colors.qualitative.Alphabet has 26 colors avaliable, but looks
  bad when there are less than 5 drivers. Color switches should be done accordingly.
  
  Args:
    tasks: A pandas dataframe with each row containing a single task.
  
  Returns:
    driver_colors: Dictionary with each driver as a string key and their 
                   string color HEX code as a value.
  
  Raises:
    ValueError: Driver color selection accomodates a max of 10 drivers.
                Please add additional colors for each additional driver
                past 10 or swap to Plotly's Alphabet color swatch.

  """
  driver_colors = {}
  driver_names = tasks['Driver'].unique()

  if len(driver_names) > 10:
    raise ValueError('''Driver color selection accomodates a max of 26 drivers.
            Please add additional colors for each additional driver past 26.''')
  else:
    for idx, driver in enumerate(driver_names):
      driver_colors[driver] = px.colors.qualitative.Plotly[idx]
  return driver_colors

def create_task_lines(tasks, end_date, lookback_period, driver_colors):
  """Creates a line chart containing the total tasks completed by each driver each day.
  
  Args:
    tasks: A pandas dataframe with each row containing a single task.
    end_date: The last datetime date that determines how far back the data will be included in the graph.
    lookback_period: A string that is used to set the title of the graph. It is correlated to the end date.
    driver_colors: Dictionary with each driver as a string key and their 
                   string color HEX code as a value.

  Returns:
    fig: Plotly object containing the graph figure
  """

  df = tasks[tasks['Status'] == 'Completed']
  df = df[df['Creation Date'] >= end_date]

  df['Start Date'] = tasks['Start Time'].dt.floor('d')
  df = df.groupby(['Driver', 'Start Date']).count().reset_index()
  fig = px.line(df,
                x='Start Date',  # Would be more accurate using Start Time (Start Date)
                y='Task No',
                color='Driver',
                color_discrete_map=driver_colors,
                title=f'Historical Driver Performances ({lookback_period})',
                labels={'Start Date': 'Date',
                       'Task No': 'Tasks Completed'})
  
  hovertemp = ('%{y} Tasks Completed')
  fig.update_traces(hovertemplate=hovertemp, mode='markers+lines')
  fig.update_layout(hovermode="x unified",
                    plot_bgcolor='white',
                    font_family='Roboto',
                    font_color='black',
                    autosize=True)
  fig.update_yaxes(gridcolor='#808080')
  return fig

def get_top_10_tasks_dropdown(tasks, end_date):
  """Gets the top 10 most common tasks for the HTML dropdown selection."""
  df = tasks[tasks['Creation Date'] >= end_date]
  times_completed = df['Part No'].value_counts()[:10]
  top_10_tasks = times_completed.index.to_numpy()

  for rank, task in enumerate(top_10_tasks):
    top_10_tasks[rank] = str(rank+1) + '. ' + task

  return top_10_tasks, top_10_tasks[0]

def create_dur_dist_bars(tasks,
                         task_info,
                         end_date,
                         lookback_period,
                         driver_colors):
  """Creates a bar graph containing the average duration and distance by each driver to complete the given task.
  
  Args:
    tasks: A pandas dataframe with each row containing a single task.
    task_info: A string that contains the rank and task name of the task.
               For example, task_info="2. 74110-T20-A000-HCM" means that 
               it was the second most common task seen and its task name is
               "74110-T20-A000-HCM".
    end_date: The last datetime date that determines how far back the data will be included in the graph.
    lookback_period: A string that is used to set the title of the graph. It is correlated to the end date.
    driver_colors: Dictionary with each driver as a string key and their 
                   string color HEX code as a value.

  Returns:
    fig: Plotly object containing the graph figure
  """

  df = tasks[tasks['Status'] == 'Completed']
  df = df[df['Creation Date'] >= end_date]

  task_name, rank = _parse_task_info(task_info)
  df = df[df["Part No"] == task_name]
  task_type = df["Task Type"].iloc[0]
  times_completed = df['Driver'].value_counts()

  df = df.groupby('Driver').mean()
  df['Duration'] = round(df['Duration'] / 60, 2)
  df['Distance'] = round(df['Distance'], 2)
  
  mean_dur = np.mean(df['Duration'])
  mean_dist = np.mean(df['Distance'])

  fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.1)

  drivers = df.index
  dur_hovertemp = "Driver: %{x} <br>Avg Duration: %{y} mins <br>Completed: %{customdata} time(s)<extra></extra>"
  dist_hovertemp = "Driver: %{x} <br>Avg Distance: %{y} meters <br>Completed: %{customdata} time(s)<extra></extra>"

  for driver in drivers:
    driver_data = df.loc[driver]
    color = driver_colors[driver]

    fig.add_trace(go.Bar(x=[driver],
                         y=[driver_data['Duration']],
                         name=driver,
                         hovertemplate=dur_hovertemp,
                         customdata=[times_completed.loc[driver]],
                         text=f"{driver_data['Duration']:.2f}",
                         textposition='inside',
                         marker_color=color,
                         legendgroup=driver,
                         showlegend=False),
                  row=1, col=1)

    fig.add_trace(go.Bar(x=[driver],
                         y=[driver_data['Distance']],
                         name=driver,
                         hovertemplate=dist_hovertemp,
                         customdata=[times_completed.loc[driver]],
                         text=f"{driver_data['Distance']:.1f}",
                         textposition='inside',
                         marker_color=color,
                         legendgroup=driver),
                  row=1, col=2)
  
  # Add the mean lines to the subplots
  fig.add_trace(go.Scatter(x=[drivers[0], drivers[-1]],
                           y=[mean_dur, mean_dur],
                           cliponaxis=True,
                           mode='lines',
                           line=dict(color='green', width=2, dash='solid'),
                           name=f'Avg {mean_dur:.2f} mins',
                           hovertemplate=f'Average {mean_dur:.2f} mins<extra></extra>'),
                row=1, col=1)

  fig.add_trace(go.Scatter(x=[drivers[0], drivers[-1]],
                           y=[mean_dist, mean_dist],
                           cliponaxis=True,
                           mode='lines',
                           line=dict(color='blue', width=2, dash='solid'),
                           name=f'Avg {mean_dist:.1f} m',
                           hovertemplate=f'Average {mean_dist:.1f} meters<extra></extra>'),
                row=1, col=2)

  # Configure individual axis titles
  fig.update_xaxes(title_text="Durations", row=1, col=1)
  fig.update_xaxes(title_text="Distances", row=1, col=2)
  fig.update_yaxes(title_text="Average Duration (minutes)", row=1, col=1)
  fig.update_yaxes(title_text="Average Distance (meters)", row=1, col=2)  #  mirror='all', side='right', can mirror yaxis but would overlap with legend bug

  # Configure layout
  fig.update_layout(title_text=f"Average Duration and Distance for Task {rank} - Completed {sum(times_completed)} Times - {task_type} ({lookback_period})",
                    barmode='group',
                    plot_bgcolor='white',
                    font_family='Roboto',
                    font_color='black',
                    autosize=True)
  fig.update_yaxes(gridcolor='#808080')
  return fig

def _parse_task_info(task_info):
  """Parses the given task information for its task name and its rank (rank 1 means it was the most common task)."""
  task_name = re.search(r'(?<=[\d+]. ).*', task_info)[0]
  rank = re.search(r'\d+', task_info)[0]
  return task_name, rank

def create_task_pi(tasks,
                   end_date,
                   lookback_period,
                   driver_colors):
  """Creates a pi chart containing the total distribution of completed tasks by each driver."""
  df = tasks[tasks['Status'] == 'Completed']
  df = df[df['Creation Date'] >= end_date]

  count_df = df.groupby('Driver').count().reset_index()
  count_df['Perc'] = (count_df['Task No'] / count_df['Task No'].sum()).apply(lambda x: f'{x:.2%}')

  fig = px.pie(count_df, 
               values='Task No',
               names='Driver',
               color='Driver',
               color_discrete_map=driver_colors,
               hover_data=['Driver', 'Task No', 'Perc'],
               title=f'Driver Task Percentages ({lookback_period})')
  
  hovertemp = ('Driver: %{customdata[0][0]} <br>Total Tasks Completed: %{customdata[0][1]} <br>Percentage of Total Tasks: %{customdata[0][2]} ')
  fig.update_traces(hovertemplate=hovertemp)
  fig.update_layout(autosize=True,
                    font_family='Roboto',
                    font_color='black',
                    legend={'title':'Task Types',
                            'yanchor': 'bottom',
                            'y': 0.1,
                            'xanchor': 'right',
                            'x': 2.0})
  return fig

def create_efficiency_table(tasks, end_date):
  """Creates an efficiency table to display key statistics for each driver.

  Args:
    tasks: A pandas dataframe with each row containing a single task.
    end_date: The last datetime date that determines how far back the data will be included in the graph.

  Returns:
    driver_table: A pandas dataframe containing key statistics on each driver.
  """
  
  df = tasks[tasks['Status'] == 'Completed']
  df = df[df['Creation Date'] >= end_date]

  driver_table = []
  count_df = df.groupby('Driver').count().reset_index()
  sum_df = df.groupby('Driver').sum().reset_index()

  for idx in range(len(count_df)):
    tasks_by_driver = count_df.iloc[idx]['Task No']

    if sum_df.iloc[idx]['Duration'] != 0:
      dur_task_ratio = sum_df.iloc[idx]['Duration'] / tasks_by_driver
      dur_task_ratio = f'{dur_task_ratio:.2f}'
    else:
      dur_task_ratio = 'Insufficient Data'

    if sum_df.iloc[idx]['Distance'] != 0:
      dist_task_ratio = sum_df.iloc[idx]['Distance'] /  tasks_by_driver
      dist_task_ratio = f'{dist_task_ratio:.2f}'
    else:
      dist_task_ratio = 'Insufficient Data'

    driver_table.append([count_df.iloc[idx]['Driver'], tasks_by_driver, dur_task_ratio, dist_task_ratio])

  driver_table = pd.DataFrame(driver_table, columns=['Driver', 'Total Tasks', 'Duration-Task Ratio', 'Distance-Task Ratio']).sort_values('Driver')
  return driver_table