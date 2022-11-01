import calendar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px

DIRECTION_NAMES = ("N","NNE","NE","ENE"
                   ,"E","ESE","SE","SSE"
                   ,"S","SSW","SW","WSW"
                   ,"W","WNW","NW","NNW")

def windrose_histogram(wspd, wdir, speed_bins=12, normed=False, norm_axis=None):
    
    if isinstance(speed_bins, int):
        speed_bins = np.linspace(0, wspd.max(), speed_bins)
        
    num_spd = len(speed_bins)
    num_angle = 16
    
    
    wdir_shifted = (wdir + 11.25) % 360

    angle_bins = np.linspace(0, 360, num_angle + 1)
    hist, *_ = np.histogram2d(wspd, wdir_shifted, bins=(speed_bins, angle_bins))
    if normed:
        hist /= hist.sum(axis=norm_axis, keepdims=True)
        hist *= 100
    
    return hist, angle_bins, speed_bins
    
        
def plot_wind_polar_frequency(wspd, wdir, subdivs = 10):
    
    hist, angle_bins, spd_bins = windrose_histogram(wspd, wdir)
    angle_bins_fine = np.linspace(0, 360, (len(angle_bins) - 1) * subdivs + 1)

    A, R = np.meshgrid(np.deg2rad((angle_bins_fine - 11.25) % 360), spd_bins)

    hist[hist < 1] = np.nan
    
    
    
    fig, axis = plt.subplots(ncols=1, subplot_kw=dict(projection="polar"))
    axis.tick_params(axis='y', labelcolor='white')
    xticks = np.deg2rad((angle_bins - 11.25) % 360)


    
    for pos in xticks:
        axis.plot([pos]*2, [0, spd_bins.max()], 'k:', lw=1, zorder=-1)
        
    for pos in spd_bins[1:-1]:
        x = np.linspace(0, 2*np.pi, 50)
        y = np.zeros(50)+pos
        axis.plot(x, y, 'k:', lw=1, zorder=-1)
    
    pc = axis.pcolormesh(A, R, np.repeat(hist, subdivs, axis=1), cmap='Spectral_r')
    
    
    axis.set_rmax(spd_bins.max())
    

    
    axis.set_theta_zero_location('N')
    axis.set_theta_direction(-1)
    
    axis.set_xticks(xticks, minor=True)
    axis.set_xticks(np.linspace(0, 2 * np.pi, 16, endpoint=False), minor=False)
    axis.set_yticks(spd_bins, minor=True)
 
    axis.set_xticklabels(DIRECTION_NAMES, minor=False);
    axis.set_facecolor(color='#e4e6e8');
    
    for key in axis.spines:
        axis.spines[key].set_color('#e4e6e8')
    
    axis.set_title('Polar histogram of windspeed and direction', fontsize=12)
    
    yticklb = axis.get_yticklabels()
    for i in yticklb:
        i.set_color('black')
    axis.set_rlabel_position(145)
    
    axis.grid(False)
    
    cb = fig.colorbar(pc, ax=axis, fraction=0.03, pad=0.2)
    cb.ax.tick_params(labelsize=8)

    for i in axis.get_xticklabels() + axis.get_yticklabels():
        i.set_fontsize(8)
    
    
    return fig
    

def plot_hexbin(wspd, wdir, gridsize=25):
    fig, axis = plt.subplots(ncols=1)
    # Shift so that angles in [348.75, 360) and in [0, 11.25) are binned together
    # and in general angles are in bins [a-11.25, a+11.25) (modulo 360) for a=0, 22.5, ..., 337.5
    hb = axis.hexbin((wdir + 11.25) % 360, wspd, gridsize=gridsize, cmap='Spectral_r', mincnt=1)
    axis.set_xlim(-11.25, 360 - 11.25)
    axis.set_xticks(np.linspace(0, 360, 8, endpoint=False))
    axis.set_ylim(wspd.min(), wspd.max())
    axis.set_xlabel("Wind direction by compass angle [oN]")
    axis.set_ylabel("Wind speed (m/s)");
    axis.set_title('Hexagonal bin histogram of windspeed and direction', fontsize=12); 
    cb = fig.colorbar(hb)
    cb.ax.tick_params(labelsize=8)
    
    for i in axis.get_xticklabels() + axis.get_yticklabels():
        i.set_fontsize(8)
    
    return fig

def make_wind_df(wspd, wdir, num_partitions, max_speed=None, normed=False, norm_axis=None):
    if max_speed is None:
        speed_bins = np.linspace(0, wspd.max(), num_partitions + 1)
    else:
        # Add an extra partition to include everything else
        speed_bins = np.append(np.linspace(0, max_speed, num_partitions + 1), np.inf)
        
    h, *_ = windrose_histogram(wspd, wdir, speed_bins, normed=normed, norm_axis=norm_axis)
    
    
    wind_df = pd.DataFrame(
        data=h, columns=DIRECTION_NAMES
    )
    
    speed_bin_names = []
    speed_bins_rounded = [round(i, 2) for i in speed_bins]
    for start, end in zip(speed_bins_rounded[:-1], speed_bins_rounded[1:]):
        speed_bin_names.append(
            f'{start:g}-{end:g}' if end < np.inf else f'>{start:g}'
        )
    
    wind_df['strength'] = speed_bin_names
    
    wind_df = wind_df.melt(
        id_vars=['strength'],
        var_name='direction',
        value_name='frequency'
    )
    
    return wind_df

def plot_line_windrose(wspd, wdir, num_partitions=4, max_speed=4, month=None):
    wind_df = make_wind_df(wspd=wspd, wdir=wdir, 
        num_partitions=num_partitions, max_speed=max_speed,
        normed=True)
    wind_df['frequency'] = wind_df['frequency'] / 100
    fig = px.line_polar(wind_df, r="frequency", theta="direction", color="strength", line_close=True,
                        color_discrete_sequence=px.colors.sequential.Magma_r,
                        template="plotly_dark",
                        title='Wind rose - line format ({})'.format(
                            calendar.month_name[month] if month in range(1, 13) else 'Annual'
                        )
                    )

    fig.update_polars(
        radialaxis_angle = -45,
        radialaxis_tickangle=-45,
        radialaxis_tickformat=',.0%',
        radialaxis_tickfont_color='white',
    )
    return fig

def plot_bar_windrose(wspd, wdir, num_partitions=4, max_speed=4, month=None):
    wind_df = make_wind_df(wspd=wspd, wdir=wdir, 
                        num_partitions=num_partitions, 
                        max_speed=max_speed, 
                        normed=True)
    wind_df['frequency'] = wind_df['frequency'] / 100
    fig = px.bar_polar(wind_df, r="frequency", theta="direction", color="strength",
                        color_discrete_sequence=px.colors.sequential.Magma_r,
                        template="plotly_dark",
                        title='Wind rose - bar format ({})'.format(
                            calendar.month_name[month] if month in range(1, 13) else 'Annual'
                        )
                    )


    fig.update_polars(
        radialaxis_angle = -45,
        radialaxis_tickangle=-45,
        radialaxis_tickformat=',.0%',
        radialaxis_tickfont_color='white',
    )
    
    return fig
