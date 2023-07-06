import numpy as np
import pandas as pd

## Convert from R to Python
# wet_bulb_temp <- function ( temp, rh ) { 
# wbt <- temp * atan2(0.151977*sqrt(rh+8.313659),1) + atan2(temp+rh,1) - atan2(rh-1.676331,1) + 0.00391838*rh**(1.5)*atan2(0.023101*rh,1) - 4.686035 ;
# return( wbt )
# }

def wet_bulb_temp(temp, rh):
    wbt = temp * np.arctan2(0.151977*np.sqrt(rh+8.313659),1) + np.arctan2(temp+rh,1) - np.arctan2(rh-1.676331,1) + 0.00391838*rh**(1.5)*np.arctan2(0.023101*rh,1) - 4.686035
    return( wbt )


# abs_humid <- function ( t, e ) { 
# zero_degC <- 273.15 ;
# gas_constant <- 8.3144598 ; 
# # ah <- 18.015/gas_constant*e/(t+zero_degC); # water vapor @ wbt [g/m3]
# ah <- 18./gas_constant*e/(t+zero_degC); # water vapor @ wbt [g/m3]
# return ( ah )
# }

def abs_humid(t, e):
    zero_degC = 273.15
    gas_constant = 8.3144598
    ah = 18./gas_constant*e/(t+zero_degC) # water vapor @ wbt [g/m3]
    return ah

# wexler_hyland <- function (t) {
# Tabs <- t + 273.15
# p <- exp ( -0.58002206e4 / Tabs +0.13914993e1 -0.48640239e-1 * Tabs +0.41764768e-4 * Tabs**2 -0.14452093e-7 * Tabs**3 +0.65459673e1 * log(Tabs) ) ;
# return (p) 
# }

def wexler_hyland(t):
    Tabs = t + 273.15
    p = np.exp ( -0.58002206e4 / Tabs +0.13914993e1 -0.48640239e-1 * Tabs +0.41764768e-4 * Tabs**2 -0.14452093e-7 * Tabs**3 +0.65459673e1 * np.log(Tabs) )
    return p

# water_ev <- function ( temp, dewp ) {

# e_temp <- wexler_hyland ( temp )
# e_dewp <- wexler_hyland ( dewp )
# ah_temp <- abs_humid ( temp, e_temp )
# ah_dewp <- abs_humid ( dewp, e_dewp )
# rh <- e_dewp/e_temp * 100

# wbt <-  wet_bulb_temp ( temp, rh )
# e_wbt <- wexler_hyland ( wbt )
# ah_wbt <- abs_humid ( wbt, e_wbt )

# delta_ah_wbt <- ah_wbt - ah_dewp

# return ( delta_ah_wbt )
# }

def water_ev(temp, dewp):
    e_temp = wexler_hyland(temp)
    e_dewp = wexler_hyland(dewp)
    ah_temp = abs_humid(temp, e_temp)
    ah_dewp = abs_humid(dewp, e_dewp)
    rh = e_dewp/e_temp * 100
    wbt = wet_bulb_temp(temp, rh)
    e_wbt = wexler_hyland(wbt)
    ah_wbt = abs_humid(wbt, e_wbt)
    delta_ah_wbt = ah_wbt - ah_dewp
    return delta_ah_wbt

def johatsu(kakudo, n, delta_ah_wbt, wspd, wdir, yearhour):
    u_pad = 0.309 * wspd * np.abs(np.cos((wdir - kakudo) * np.pi / 180.))
    water_evap = delta_ah_wbt * u_pad * 3.6 * koritsu(u_pad)
    water_evap_accum = np.zeros(n)
    for i in range(1, n):
        water_evap_accum[i] = (water_evap_accum[i-1] + (water_evap[i-1] + water_evap[i]) * 0.5 
        * ( (yearhour[i] - yearhour[i-1]) if (yearhour[i] - yearhour[i-1]) <= 6 else 0))
    water_evap_accum = water_evap_accum/1000.
    # print(' ... water_evap [kg/m2/hr] & water_evap_accum [t/m2] ... ')
    return pd.DataFrame({'water_evap': water_evap, 'water_evap_accum': water_evap_accum})


def koritsu(u):
    c1 = 0.955021
    c2 = -0.18525
    c3 = 0.452404
    eta = c1 + c2*np.exp(c3*np.log(u))
    return eta

# table_stations_nearby <- renderDataTable({
# #    source("leaflet/r.func.geo")
#     keido_ido_kaibatsu <- NULL ; keido_ido_kaibatsu <- geocode(input$stname)
#     distance <- NULL ; distance <- array(1e10,dim = nrow(stid_org))
#     for (i in 1:nrow(distance)) {
# #      distance[i] <- ((stid_org$lat)[i] - keido_ido_kaibatsu$lat)^2 + ((stid_org$lon)[i] - keido_ido_kaibatsu$lon)^2
#       distance[i] <- ((stid_org$lat)[i] - as.numeric(input$stlat))^2 + ((stid_org$lon)[i] - as.numeric(input$stlng))^2
#     }
#     stid_org_distance <-NULL ; stid_org_distance <- data.frame (stid_org,distance)
#     require(data.table)
#     data_final <- NULL
#     data_final <- data.table(stid_org_distance,key="distance")[1:40]
#     data_final <- data_final[,-"label"] 
#     data_final <- data_final[,-"country"] 
#     data_final <- data_final[,-"distance"] 
# #    data_final <- data_final[,-"stid2"] 
#   }, options = list(pageLength = 4))

def get_stations_nearby(df, lat, lon, nstations=40):
    distance = (df.lat - lat) ** 2 + (df.lon - lon) ** 2
    return df.assign(distance=distance).sort_values(by='distance').head(nstations)

