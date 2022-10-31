import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

from funcs import johatsu


def plot_temperature(yearday, temp, wbt):
    df = pd.DataFrame({"yearday":yearday,"Temperature":temp,"Wet Bulb Temperature":wbt})
    df = df.melt(id_vars=["yearday"],value_vars=["Temperature","Wet Bulb Temperature"])
    fig = px.line(df, x="yearday", y="value", color='variable',
    color_discrete_sequence=px.colors.qualitative.Set1,
     labels={
        "yearday": "Day of Year",
     })
    return fig
    # TODO: add title

def plot_humid(yearday, rh):
    df = pd.DataFrame({"yearday":yearday,"Relative Humidity (%)":rh})
    df = df.melt(id_vars=["yearday"],value_vars=["Relative Humidity (%)"])
    fig = px.line(df, x="yearday", y="value", color='variable',
      color_discrete_sequence=['#339900'],
     labels={
        "yearday": "Day of Year",
     })
    return fig
    # TODO: add title

# Convert the following from R 
def plot_water_evap3(n_orientation, *args):
#     n <- as.numeric(input$n_orientation) ;
   n = n_orientation
#     kaku_pad <- double (n*2+1)
   kaku_pad = np.zeros(n*2 + 1)
#     water_evap_annual <- kaku_pad
   water_evap_annual = np.zeros_like(kaku_pad)
#     for ( j in 1:n ) { 
#       kaku <- 180.*(j-1.)/n 
#       kaku_pad [j] <- kaku
#       water_evap_annual[j] <- tail (johatsu ( kaku )$water_evap_accum,n=1) 
#       kaku_pad [j+n] <- kaku + 180.
#       water_evap_annual[j+n] <- water_evap_annual[j]
#     }
   for j in range(n):
      kaku = 180. * j / n
      kaku_pad[j] = kaku
      water_evap_annual[j] = johatsu(kaku, *args).water_evap_accum.tail(1)
      kaku_pad[j + n] = kaku + 180.
      water_evap_annual[j + n] = water_evap_annual[j]
#     j <- 2*n+1
#     kaku_pad [j] <- kaku_pad[j-n]+180.
#     water_evap_annual[j] <- water_evap_annual[j-n]
   j = 2 * n
   kaku_pad[j] = kaku_pad[j-n] + 180.
   water_evap_annual[j] = water_evap_annual[j-n]
   
#     foo <- rbind(
#       data.frame(x=kaku_pad,y=water_evap_annual)
#     )
   df = pd.DataFrame({'x': kaku_pad, 'y': water_evap_annual})  
#     # print(ggplot(foo,aes(x=x,y=y),col="orange")+geom_line())
#     g<-ggplot(foo,aes(x=kaku_pad,y=value,color=variable))
#     g<-g+geom_line(aes(y=water_evap_annual,col="Water evaporation")) 
#     g<-g+scale_colour_manual(values = c("#333399")) 
#     g <- g + xlab("Orientation (°N)") 
#     g <- g + ylab(expression("Annual water evaporation ("~t/m^2/yr~")"))
#     #    g <- g + ggtitle(paste0(noaa_stid(input$usaf,input$wban)," ",input$toshi," ",input$stname,sep=""))
#     g <- g + ggtitle(paste0(noaa_stid(input$usaf,input$wban)," year:",input$toshi," lat:",input$stlng," lng:",input$stlng,sep=""))
#     g <- g + scale_x_continuous(name = "Orientation (°N)",
#                        breaks = seq(0, 360, 45),
#                        limits=c(0, 360))
#     plot(g)
   fig = px.line(df, 
      x="x", 
      y="y", 
      labels={
         "x": "Orientation (°N)",
         "y": "Annual water evaporation (t/m^2/yr)"
      },
      title=f"No. points: {n_orientation}"
   )
   fig.update_traces(line_color="#333399")
   fig.update_xaxes(tickvals=np.arange(0, 405, 45))
   return fig



#   output$Mizu2<-renderPlot({
#     water_evap_accum <- (johatsu ( as.numeric(input$kaku) ) )$water_evap_accum
#     foo <- rbind(
#       data.frame(temp='rh',x=yearday,y=water_evap_accum)
#     )
#     # print(ggplot(foo,aes(x=x,y=y),col="orange")+geom_line())
#     g<-ggplot(foo,aes(x=yearday,y=value,color=variable))
#     g<-g+geom_line(aes(y=water_evap_accum,col="Water evaporation")) 
#     g<-g+scale_colour_manual(values = c("#333399")) 
#     g <- g + xlab("Day of year (day)") + ylab("Accumulated water evaporation (t/m^2)")
#     g <- g + ggtitle(paste0(input$kaku))
#     plot(g)
#   }) 
def plot_water_evap12(kaku, yearday, rh, *args, accum=False):
   colm = "water_evap%s" % ("_accum" if accum else "")
   water_evap_colm = johatsu(kaku, *args)[colm]
   df = pd.DataFrame(
      {
         "temp": rh,
         "x":yearday,
         "y": water_evap_colm
      }
   )
   # ggplot(foo,aes(x=yearday,y=value,color=variable))
   units = "t/m^2" if accum else "kg/m2/hr"
   fig = px.line(
      df, x="x", y="y",
      labels={
         "x": "Day of year (day)",
         "y": "%sater evaporation (%s)"%("Accumulated w" if accum else "W", units)
      },
      title='Orientation: %s°N' % kaku
   )
   fig.update_traces(line_color="#333399")
   return fig

def plot_water_evap2(kaku, *args):
   return plot_water_evap12(kaku, *args, accum=True)

def plot_water_evap1(kaku, *args):
   return plot_water_evap12(kaku, *args, accum=False)
   

def plot_wind1(wspd, wdir):
   df = pd.DataFrame({"wdir": wdir, "wspd": wspd})
   fig = px.scatter(
      df, x="wdir", y="wspd",
      labels={
         "wdir": "Wind direction in compass angle (°)",
         "wspd": "Wind speed (m/s)"
      }
   )
   fig.update_traces(marker_color="#339900", marker_opacity=0.1)
   fig.update_xaxes(range=[-6, 366])
   return fig


def plot_wind2(yearday, wspd):
   df = pd.DataFrame({"yearday": yearday, "wspd": wspd})
   fig = px.scatter(
      df, x="yearday", y="wspd",
      labels={
         "yearday": "Day of year (day)",
         "wspd": "Wind speed (m/s)"
      }
   )
   fig.update_traces(marker_color="#339900", marker_opacity=0.1)
   fig.update_xaxes(range=[-5, 370])
   return fig


def plot_wind3(yearday, wdir):
   df = pd.DataFrame({"yearday": yearday, "wdir": wdir})
   fig = px.scatter(
      df, x="yearday", y="wdir",
      labels={
         "yearday": "Day of year (day)",
         "wdir": "Wind direction (°)"
      }
   )
   fig.update_traces(marker_color="#339900", marker_opacity=0.1)
   fig.update_xaxes(range=[-5, 375])
   fig.update_yaxes(range=[-6, 372])
   return fig
   