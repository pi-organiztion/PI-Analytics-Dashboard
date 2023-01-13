"""Generates work center analytics (statistics, graphs, and tables) for the analytics dashboard.

Functions:
  generate_stat_block_values(tasks):
    Generates the key values that are displayed at the top of the analytics dashboard.

  create_task_bars(tasks,
                   wc_range,
                   end_date, 
                   lookback_period,
                   colorscale):
    Creates a bar graph containing the task counts for each work center.

  _sort_wc_names(df, drop_col=False):
    Sorts work center names by ascending assembly number.

  _filter_out_wc(df, wc_range):
    Filters out work centers not in the given range.

  _create_shorthand_wc_names(df):
    Creates shorthand work center names.

  create_task_type_bars(tasks,
                        wc_range,
                        end_date,
                        lookback_period,
                        task_type_colors):
    Creates a bar graph containing the task type counts for each work center.

  create_queue_bars(tasks,
                    wc_range,
                    end_date,
                    lookback_period,
                    colorscale):
    Creates a bar graph containing the average queue times for each work center.

  create_rollover_queue_bars(tasks,
                             rollover_period,
                             wc_range,
                             end_date,
                             lookback_period,
                             colorscale):
    Creates a bar graph containing the rollover count for each work center.

  create_task_type_pi(tasks,
                      end_date,
                      lookback_period,
                      task_type_colors):
    Creates a pi chart containing the total distribution of task types for all tasks.

  get_top_10_tasks_dropdown(tasks, end_date):
    Gets the top 10 most common tasks for the HTML dropdown selection.

  create_task_time_distrib(tasks, task_info, end_date):
    Creates a task time distribution for the given task information.

  _parse_task_info(task_info):
    Parses the given task information.

  create_efficiency_table(tasks, end_date):
    Creates an efficiency table to display key statistics for each work center.
"""

import re
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

def generate_stat_block_values(tasks):
  """Generates the stat block values that are displayed at the top of the analytics dashboard.
  
  Args:
    tasks: A pandas dataframe with each row containing a single task.

  Returns:
    stat_block_values: list of integers, given as 
                       [tasks_completed_today, tasks_currently_queued, tasks_completed_month,
                       avg_tasks_per_day, avg_tasks_per_month]
  """
  
  completed_tasks = tasks[tasks['Status'] == 'Completed']
  
  # Collect latest date information
  current_date = tasks['Creation Date'].iloc[0]
  today_tasks = tasks[tasks['Creation Time'] >= current_date]

  month_start = current_date.strftime("%Y-%m-01")
  current_month = current_date.month

  # Collect tasks completed and in-progress
  tasks_completed_today = sum(today_tasks['Status'] == 'Completed')
  tasks_currently_queued = sum(today_tasks['Status'] == 'Waiting') + sum(today_tasks['Status'] == 'In-Progress')
  tasks_completed_month =len(completed_tasks[completed_tasks['Creation Time'] >= month_start])

  # Collect average tasks completed (per day and per month)
  avg_tasks_per_day = (completed_tasks.groupby(completed_tasks['Creation Date'], sort=False)
                        .count()
                        .drop(current_date)
                        .mean())['Task No']
  avg_tasks_per_month = (completed_tasks.groupby(completed_tasks['Creation Time'].dt.month, sort=False)
                          .count()
                          .drop(current_month)
                          .mean())['Task No']
  
  stat_block_values  = [tasks_completed_today, tasks_currently_queued, tasks_completed_month,
                        int(avg_tasks_per_day), int(avg_tasks_per_month)]  
  return stat_block_values 

def create_task_bars(tasks,
                     wc_range,
                     end_date, 
                     lookback_period,
                     colorscale):
  """Creates a bar graph containing the task counts for each work center.
  
  Args:
    tasks: A pandas dataframe with each row containing a single task.
    wc_range: A list containing two integers. The first integer denotes the initial work
              center and the second integer denoites the last work center. Only work center
              numbers between and including these two integers will be displayed on the graph.
    end_date: The last datetime date that determines how far back the data will be included in the graph.
    lookback_period: A string that is used to set the title of the graph. It is correlated to the end date. 
    colorscale: A list of hexcode strings that determine the colors used in the graph.

  Returns:
    fig: Plotly object containing the graph figure
  """

  df = tasks[tasks['Status'] == 'Completed']
  df = df[df['Creation Date'] >= end_date]
  
  df = (df.groupby('Work Center', sort=False)
          .count()
          .reset_index())
  yaxis_max = max(df['Task No'])

  df = _sort_wc_names(df)
  df = _filter_out_wc(df, wc_range)
  df = _create_shorthand_wc_names(df)
  
  fig = px.bar(df,
               x='Work Center Shorthand',
               y='Task No',
               color='Task No',
               color_continuous_scale=colorscale,
               title=f'Work Centers and Completed Tasks ({lookback_period})',
               text='Task No',
               range_color=[0, yaxis_max],
               labels={'Work Center Shorthand': 'Work Centers',
                       'Task No': 'Tasks Completed'},
               hover_data=['Work Center'])
  
  hover_template = 'Work Center: %{customdata} <br>Tasks Completed: %{y}'
  fig.update_traces(hovertemplate=hover_template, textposition='inside')
  fig.update_layout(plot_bgcolor='white',
                    yaxis_range=[0, yaxis_max],
                    autosize=True,
                    font_family='Roboto',
                    font_color='black',
                    coloraxis_colorbar={'title': None,
                                        'tickvals': [],
                                        'ticktext': []})
  fig.update_yaxes(gridcolor='#808080', fixedrange=True)
  fig.update_xaxes(fixedrange=True)
  return fig

def _sort_wc_names(df, drop_col=False):
  """Sorts work center names by ascending assembly number."""
  df['Assembly No'] = df['Work Center'].apply(lambda x: int(re.search(r'[0-9]+', x)[0]))
  df = df.sort_values('Assembly No')
  if drop_col == True:
    df = df.drop(columns='Assembly No')
  return df

def _filter_out_wc(df, wc_range):
  """Filters out work centers not in the given range."""
  wc_range = np.arange(wc_range[0], wc_range[1]+1)
  df= df[df['Assembly No'].isin(wc_range)]
  return df

def _create_shorthand_wc_names(df):
  """Creates shorthand work center names."""
  df['Work Center Shorthand'] = df['Work Center'].str.replace('Assembly', 'A')
  return df

def create_task_type_bars(tasks,
                          wc_range,
                          end_date,
                          lookback_period,
                          task_type_colors):
  """Creates a bar graph containing the task type counts for each work center.
  
  Args:
    tasks: A pandas dataframe with each row containing a single task.
    wc_range: A list containing two integers. The first integer denotes the initial work
              center and the second integer denoites the last work center. Only work center
              numbers between and including these two integers will be displayed on the graph.
    end_date: The last datetime date that determines how far back the data will be included in the graph.
    lookback_period: A string that is used to set the title of the graph. It is correlated to the end date.
    task_type_colors: Dictionary with each task type as a string key and their 
                      string color HEX code as a value.

  Returns:
    fig: Plotly object containing the graph figure
  """
                  
  df = tasks[tasks['Status'] == 'Completed']
  df = df[df['Creation Date'] >= end_date]

  df = (df.groupby(['Work Center', 'Task Type'], sort=False)
        .count()
        .reset_index())

  df = _sort_wc_names(df)
  df = df.sort_values(['Assembly No', 'Task Type'])
  df = _filter_out_wc(df, wc_range)
  df = _create_shorthand_wc_names(df)

  fig = px.bar(df,
               x='Work Center Shorthand',
               y='Task No',
               color='Task Type',
               color_discrete_map=task_type_colors,
               barmode='group',
               title=f'Work Centers and Task Types Completed ({lookback_period})',
               text='Task No',
               labels={'Work Center Shorthand': 'Work Centers',
                       'Task No': 'Task Types Completed'},
               hover_data=['Work Center', 'Task Type'])

  hover_template = 'Work Center: %{customdata[0]} <br>Task Type: %{customdata[1]} <br>Tasks Completed: %{y} <extra></extra>'
  fig.update_traces(hovertemplate=hover_template, textposition='inside')
  
  fig.update_layout(plot_bgcolor='white',
                    font_family='Roboto',
                    font_color='black',
                    autosize=True,
                    xaxis=dict(categoryorder= 'array',
                               categoryarray=df['Work Center Shorthand'].unique()),
                    yaxis=dict(gridcolor='#808080'),
                    legend=dict(title='Task Types',
                                yanchor='top',
                                y=0.99,
                                xanchor='right',
                                x=0.99))
  return fig

def create_queue_bars(tasks,
                      wc_range,
                      end_date,
                      lookback_period,
                      colorscale):
  """Creates a bar graph containing the average queue times for each work center."""
  df = tasks[tasks['Creation Date'] >= end_date]
  df = df[df['Queue Time'] <= 10000]

  df = (df.groupby('Work Center', sort=False)
        .median()
        .reset_index())

  df = _sort_wc_names(df)
  df = _filter_out_wc(df, wc_range)
  df = _create_shorthand_wc_names(df)
  
  fig = px.bar(df,
               x='Work Center Shorthand',
               y='Queue Time',
               text='Queue Time',
               title=f'Works Centers and Average Queue Times ({lookback_period})',
               color='Queue Time',
               labels={'Work Center Shorthand': 'Work Centers',
                       'Queue Time':'Average Queue Time'},
               color_continuous_scale=colorscale,
               hover_data=['Work Center'])

  hovertemp = ('Work Center: %{customdata} <br>Average Queue Time: %{y}')
  fig.update_layout(plot_bgcolor='white',
                    font_family='Roboto',
                    font_color='black',
                    autosize=True,
                    coloraxis_colorbar={'title': None,
                                        'tickvals': [],
                                        'ticktext': []})
  fig.update_traces(hovertemplate=hovertemp, textposition='inside') 
  fig.update_yaxes(gridcolor='#808080')
  return fig

def create_rollover_queue_bars(tasks,
                               rollover_period,
                               wc_range,
                               end_date,
                               lookback_period,
                               colorscale):
  """Creates a bar graph containing the rollover count for each work center."""
  df = tasks[tasks['Creation Date'] >= end_date]
  df = df[df['Queue Time'] >= rollover_period]

  df = (df.groupby('Work Center')
          .count()
          .reset_index())

  all_centers = set(tasks['Work Center'].unique())
  zero_count_centers = list(set(all_centers) - set(df['Work Center']))
  spare_df = pd.DataFrame(columns=df.columns, index=range(len(zero_count_centers))).fillna(0)
  spare_df['Work Center'] = zero_count_centers
  df = pd.concat([df, spare_df]).reset_index(drop=True)
  df = _sort_wc_names(df)
  df = _filter_out_wc(df, wc_range)
  df = _create_shorthand_wc_names(df)

  fig = px.bar(df,
               x='Work Center Shorthand',
               y='Task No',
               text='Task No',
               color='Task No',
               color_continuous_scale=colorscale,
               labels={'Work Center Shorthand': 'Work Centers'},
               title=f'Work Centers and Task Rollover ({lookback_period})',
               hover_data=['Work Center'])
  hovertemp = ('Work Center: %{customdata} <br>Tasks Over Rollover Period: %{y} ')
  fig.update_traces(hovertemplate=hovertemp, textposition='inside')
  fig.update_layout(plot_bgcolor='white',
                    font_family='Roboto',
                    font_color='black',
                    autosize=True,
                    coloraxis_colorbar={'title': None,
                                        'tickvals': [],
                                        'ticktext': []})
  fig.update_yaxes(gridcolor='#808080')
  return fig

def create_task_type_pi(tasks,
                        end_date,
                        lookback_period,
                        task_type_colors):
  """Creates a pi chart containing the total distribution of task types for all tasks."""
  df = tasks[tasks['Creation Date'] >= end_date]

  df = df['Task Type'].value_counts().reset_index()
  df.columns = ['Task Type', 'Task No']
  df['Perc'] = (df['Task No'] / df['Task No'].sum()).apply(lambda x: f'{x:.2%}')

  fig = px.pie(df, 
               values='Task No',
               names='Task Type', 
               color='Task Type',
               color_discrete_map=task_type_colors,
               title=f'Task Type Percentages ({lookback_period})',
               hover_data=['Task Type', 'Task No', 'Perc'])

  hovertemp = ('Task Type: %{customdata[0][0]} <br>Tasks: %{customdata[0][1]} <br>Percentage of Total Tasks: %{customdata[0][2]} ')
  fig.update_traces(hovertemplate=hovertemp, textposition='inside')
  fig.update_layout(autosize=True,
                    font_family='Roboto',
                    font_color='black',           
                    legend={'title':'Task Types',
                            'yanchor': 'top',
                            'y': 0.15,
                            'xanchor': 'left',
                            'x': -0.1})
  return fig

def get_top_10_tasks_dropdown(tasks, end_date):
  """Gets the top 10 most common tasks for the HTML dropdown selection."""
  df = tasks[tasks['Creation Date'] >= end_date]
  times_completed = df['Part No'].value_counts()[:10]
  top_10_tasks = times_completed.index.to_numpy()

  for rank, task in enumerate(top_10_tasks):
    top_10_tasks[rank] = str(rank+1) + '. ' + task

  return top_10_tasks, top_10_tasks[0]

def create_task_time_distrib(tasks, task_info, end_date):
  """Creates a task time distribution for the given task information.
  
  Args:
    tasks: A pandas dataframe with each row containing a single task.
    task_info: A string that contains the rank and task name of the task.
               For example, task_info="2. 74110-T20-A000-HCM" means that 
               it was the second most common task seen and its task name is
               "74110-T20-A000-HCM".
    end_date: The last datetime date that determines how far back the data will be included in the graph.

  Returns:
    fig: Plotly object containing the graph figure
  """

  bin_count = 15
  df = tasks[tasks['Creation Date'] >= end_date]

  task_name, rank = _parse_task_info(task_info)
  task_type = df[df["Part No"] == task_name]["Task Type"].iloc[0]


  task_durations = df[df['Part No'] == task_name]['Duration']
  task_durations = task_durations.rename('Tasks Count')

  mean_time = np.mean(task_durations)
  median_time = np.median(task_durations)

  # Get y-axis limits of bins
  counts, _ = np.histogram(task_durations, bins=bin_count)
  yaxis_max = max(counts) + 1

  fig = px.histogram(task_durations,
                     nbins=bin_count,
                     title=f'Task {rank} - Completed {len(task_durations)} Times - {task_type}',
                     color_discrete_sequence=['#243D76'],                 
                     text_auto=True)

  hovertemp = ('%{y} count(s) this task took<br>%{x}s to complete<extra></extra>')
  fig.update_traces(hovertemplate=hovertemp)

  fig.add_trace(go.Scatter(x=[mean_time, mean_time],
                           y=[1, yaxis_max],
                           cliponaxis=True,
                           mode='lines',                       
                           line=dict(color='red', width=2, dash='solid'),
                           name=f'Mean {mean_time/60:.1f} mins',
                           hovertemplate=f'Mean {mean_time:.1f}s<extra></extra>'))
                           
  fig.add_trace(go.Scatter(x=[median_time, median_time],
                           y=[1, yaxis_max], 
                           cliponaxis=True,                          
                           mode='lines', 
                           line=dict(color='limegreen', width=2, dash='solid'),
                           name=f'Median {median_time/60:.1f} mins',
                           hovertemplate=f'Median {median_time:.1f}s<extra></extra>'))
  
  fig.update_layout(plot_bgcolor='white',
                    font_family='Roboto',
                    font_color='black', 
                    autosize=True,
                    margin=dict(r=30),
                    legend=dict(title='Legend',
                                yanchor='top',
                                y=0.98,
                                xanchor='right',
                                x=0.98),                                
                    xaxis=dict(title='Seconds to Completion (s)',
                               fixedrange=True),                     
                    yaxis=dict(title='Completed Count',
                               gridcolor='#808080',
                               fixedrange=True))
  return fig

def _parse_task_info(task_info):
  """Parses the given task information for its task name and its rank (rank 1 means it was the most common task)."""
  task_name = re.search(r'(?<=[\d+]. ).*', task_info)[0]
  rank = re.search(r'\d+', task_info)[0]
  return task_name, rank

def create_efficiency_table(tasks, end_date):
  """Creates an efficiency table to display key statistics on each work center.
  
  Args:
    tasks: A pandas dataframe with each row containing a single task.
    end_date: The last datetime date that determines how far back the data will be included in the graph.

  Returns:
    wc_table: A pandas dataframe containing key statistics on each work center.
  """

  df = tasks[tasks['Creation Date'] >= end_date]

  median_df = df.groupby('Work Center', sort=False).median().reset_index()
  count_df = df.groupby('Work Center', sort=False).count().reset_index()
  sum_df = df.groupby('Work Center', sort=False).sum().reset_index()
  
  wc_table = []
  for idx in range(len(median_df)):
    wc = median_df.iloc[idx]['Work Center']
    total_tasks = count_df.iloc[idx]['Task No']
    avg_queue_time = median_df.iloc[idx]['Queue Time']

    if sum_df.iloc[idx]['Duration'] != 0:
      dur_task_ratio = sum_df.iloc[idx]['Duration'] / total_tasks
      dur_task_ratio = f'{dur_task_ratio:.2f}'
    else:
      dur_task_ratio = 'Insufficient Data'

    if sum_df.iloc[idx]['Distance'] != 0:
      dist_task_ratio = sum_df.iloc[idx]['Distance'] / total_tasks
      dist_task_ratio = f'{dist_task_ratio:.2f}'
    else:
      dist_task_ratio = 'Insufficient Data'

    wc_table.append([wc, total_tasks, avg_queue_time, dur_task_ratio, dist_task_ratio])

  wc_table = pd.DataFrame(wc_table, columns=['Work Center', 'Total Tasks', 'Avg Queue Time (s)', 'Duration-Task Ratio', 'Distance-Task Ratio'])
  wc_table = _sort_wc_names(wc_table, drop_col=True)
  return wc_table