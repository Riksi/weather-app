import L from 'leaflet';
import { Streamlit, RenderData } from "streamlit-component-lib"
    
    window.onload = function(){
        var locations;
        var lat = document.getElementById("lat");
        var lon = document.getElementById("lon");
        var near = document.getElementById("near");
        var clear = document.getElementById("clear");
        var ws = document.getElementById("ws");
        var prevNearest;

        function getLatLng(){
            var latval = parseFloat(lat.value);
            var lonval = parseFloat(lon.value);

            if (!(isNaN(latval) || isNaN(lonval))){
                return [latval, lonval];
            }
            else{
                return null
            }
        }

        
        var latLng = getLatLng();
        if (latLng === null){
            latLng = [47.989921667414194, 5.625]
        }

        // Streamlit.setComponentValue({
        //     "marker": latLng
        // })


        var map = L.map('map').setView(latLng, 13);
         L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        var marker = L.marker(latLng).addTo(map);

        var neighbours = [];

        function clearNear(){
            neighbours.forEach(function(n){
                map.removeLayer(n);
            });
            neighbours = [];
            clear.style.display = "none";
        }

        function sqrEuclidean(x, lat, lon){

            var dx = x['lat'] - lat;
            var dy = x['lon'] - lon;
            return dx*dx + dy*dy;
        }

        function showNear(){
            clearNear();
            // Sort by distance
            var latLng = getLatLng();

            locations.sort(function(a, b){
                return sqrEuclidean(a, latLng[0], latLng[1]) - sqrEuclidean(b, latLng[0], latLng[1]);
            }).slice(0, 10);

            let nearby = locations.slice(0, 10);
            
            clear.style.display = "inline-block";
            nearby.forEach(
                (l, idx)=>{
                    var circle = L.circleMarker(

                        [l['lat'], l['lon']],
                        // TODO: Add popup
                    ).addTo(map);
                    circle.on(
                        'click',
                        (e)=>{
                            {
                                ws.innerHTML = circle.getLatLng().lat + ", " + circle.getLatLng().lng;
                                // change color
                                circle.setStyle({color: 'red'});
                                console.log(prevNearest);
                                if(prevNearest!==undefined){
                                    prevNearest.setStyle({color: '#3388ff'});
                                }
                                prevNearest = circle;
                                L.DomEvent.stopPropagation(e);
                                Streamlit.setComponentValue({
                                    "ws": idx
                                }
                                );
                            }
                        }
                    )
                    neighbours.push(circle);
                }
            )
            map.fitBounds(neighbours.map(function(n){return n.getLatLng()}));
        }

        function changeMarker() {
            var latLng = getLatLng();

            if (latLng !== null){
                marker.setLatLng(latLng);
                map.panTo(latLng);
            }
        }

        lat.onchange = changeMarker;
        lon.onchange = changeMarker;
        near.onclick = showNear;
        clear.onclick = clearNear;
        

        map.on('click', function(e) {
            {
                var latval = e.latlng.lat;
                var lonval = e.latlng.lng;
                marker.setLatLng([latval, lonval]);
                lat.value = latval;
                lon.value = lonval;
                // Streamlit.setComponentValue({
                //     "marker": [latval, lonval]
                // }
                // );
            }
        })

        Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, (e)=>{
            locations = e.detail.args['data'];
            lat.value = e.detail.args['lat'];
            lon.value = e.detail.args['lon'];
            Streamlit.setFrameHeight();
        })

        Streamlit.setComponentReady();
        Streamlit.setFrameHeight();
    }
        
