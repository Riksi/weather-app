import L from 'leaflet';
import { Streamlit } from "streamlit-component-lib"
    
    window.onload = function(){
        // Input elements
        var latInput = document.getElementById("lat");
        var lonInput = document.getElementById("lon");
        var near = document.getElementById("near");
        var clear = document.getElementById("clear");
        var inputs = [latInput, lonInput];

        // Map
        var map;
        var marker;
        
        // Neighbours
        var locations = [];
        var neighbours = [];
        var presentNearestIdx = null;
        var init = true;
        var neighboursOf = null;
        // var isFocused = false;

        

        inputs.forEach(inp => {

            inp.onfocus = function(){
                inp.classList.add('focused')
            }
            
            inp.onblur = function() {
                inp.classList.remove('focused')
            }

        })
        

        function getState(){
            var state = {}
            state['marker'] = {
                'lat': marker.getLatLng().lat, 
                'lon': marker.getLatLng().lng
            }
            if (presentNearestIdx !== null){
                var presentNearest = neighbours[presentNearestIdx];
                state['ws'] = {
                    'idx': presentNearestIdx,
                    'lat': presentNearest.circle.getLatLng().lat, 
                    'lon': presentNearest.circle.getLatLng().lng,
                    'usaf': presentNearest.data.usaf,
                    'wban': presentNearest.data.wban
                }
            } else {
                state['ws'] = null
            }
            state['for'] = neighboursOf
            return state
        }

        function sendData(){
            Streamlit.setComponentValue(getState())
        }

        function getLatLng(){
            var latval = parseFloat(latInput.value);
            var lonval = parseFloat(lonInput.value);

            if (!(isNaN(latval) || isNaN(lonval))){
                return [latval, lonval];
            }
            else{
                return null
            }
        }

        function clearNear(){
            neighbours.forEach(function(n){
                map.removeLayer(n.circle);
            });
            neighbours = [];
            clear.style.display = "none";
            presentNearestIdx = null;
            neighboursOf = null;

            // near.value = "Find stations nearby";
        }
        
        function showNear(){
            clearNear();

            var latLng = marker.getLatLng()
            // console.log('Showing near', latLng.lat, latLng.lng)
            

            neighboursOf = {"lat": latLng.lat, "lon": latLng.lng};
            
            clear.style.display = "inline-block";
            locations.forEach(
                (l, idx)=>{
                    var circle = L.circleMarker(
                        [l['lat'], l['lon']],
                        {radius: 12}
                    ).addTo(map);
                    var before =  `<strong>${l.stname}</strong>`
                    before += `<br>USAF: ${l.usaf}, WBAN: ${l.wban}`
                    var after = `Available dates: ${l.start} to ${l.end}`
                    
                    circle.on('mouseover', ()=>{
                        showPopup(
                            circle,
                            before, after
                        )
                    })
                    circle.on('mouseout', ()=>{
                        hidePopup(circle)
                    })
                    circle.on(
                        'click',
                        (e)=>{
                            L.DomEvent.stopPropagation(e);
                            
                            // console.log('circle', latLng.lat, latLng.lng)
                            var circlelatLng = circle.getLatLng();
                            changeMapState([circlelatLng.lat, circlelatLng.lng])

                            if(presentNearestIdx != idx){

                                showPopup(
                                    circle,
                                    before, after
                                )
                                
    
                                latInput.value = circlelatLng.lat;
                                lonInput.value = circlelatLng.lng;
                                
                                if(presentNearestIdx !== null){
                                    neighbours[presentNearestIdx].circle.setStyle({color: '#3388ff'});
                                }
                                
                                circle.setStyle({color: '#f03'});
                                presentNearestIdx = idx;
                            }
                            else{
                                circle.openPopup();
                            }
                            
                            sendData();
                        }
                        
                    )
                    neighbours.push({
                        circle: circle,
                        data: l
                    });
                }
            )
            map.fitBounds(neighbours.map(function(n){return n.circle.getLatLng()}));
        }

        function roundString(x){
            return (Math.round(x * 10**4) / 10**4) + ""
        }

        function showPopup(elem, before, after){
            var lat = roundString(elem.getLatLng().lat);
            var lon = roundString(elem.getLatLng().lng);
            var content =  `Lat: ${lat}, Lon: ${lon}`
            if (before !== undefined){
                content = before + "<br>" + content;
            }
            if (after !== undefined){
                content = content + "<br>" + after;
            }
            elem.bindPopup(content).openPopup();
        }

        function hidePopup(elem){
            elem.closePopup();
        }

        function changeMapState(latLng){
            marker.setLatLng(latLng).update();
                map.panTo(latLng);
                showPopup(marker);
                // if (neighboursOf !== null){
                //     near.value = "Update";
                // }
            
        }   

        function changeMarker() {
            var latLng = getLatLng();

            if (latLng !== null){
                changeMapState(latLng);
                sendData();
            }
        }

        function onMapClick(e) {
            var latval = e.latlng.lat;
            var lonval = e.latlng.lng;

            latInput.value = latval;
            lonInput.value = lonval;
            // console.log('click', latval, lonval);

            changeMapState([latval, lonval]);
            sendData();
        }

        function initialise(lat, lon){
            var latLng = [lat, lon];

            // Map
            map = L.map('map').setView(latLng, 10);
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }).addTo(map);
            map.on('click',  onMapClick);

            // Marker
            marker = L.marker(latLng).addTo(map);

            

            marker.on('click', (e)=>{
                    showPopup(marker);
                    L.DomEvent.stopPropagation(e);
                }
            )
            marker.on('mouseover', (e)=>{
                    showPopup(marker);
                }
            )
            marker.on('mouseout', (e)=>{
                hidePopup(marker);
            })
            
            
            latInput.value = lat;
            lonInput.value = lon;
        }

        latInput.onchange = changeMarker;
        lonInput.onchange = changeMarker;
        near.onclick = showNear;
        clear.onclick = clearNear;

        Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, (e)=>{
            var data = e.detail
            locations = data.args['data'];
            
            
            // Maintain compatibility with older versions of Streamlit that don't send
            // a theme object.
            // if (data.theme) {
            //     // Use CSS vars to style our button border. Alternatively, the theme style
            //     // is defined in the data.theme object.
            //     const borderStyling = `1px solid var(${
            //     isFocused ? "--primary-color" : "gray"
            //     })`
            //     inputs.forEach(
            //         (inp)=>{
            //             inp.style.border = borderStyling
            //             inp.style.outline = borderStyling
            //         }
            //     )
            // }
            
            // if init update lat and lon
            // otherwise assert difference is small
            if (init || data.args['update']){
                var lat = data.args['lat'];
                var lon = data.args['lon'];
                if(init){
                    initialise(lat, lon);
                    init = false;
                    // console.log('RENDER_EVENT:', lat, lon);
                }
                else {
                    changeMapState([lat, lon]);
                    latInput.value = lat;
                    lonInput.value = lon;
                    clearNear();
                }
            } else{
                var eps = 1e-6;
                var latval = parseFloat(latInput.value);
                var lonval = parseFloat(lonInput.value);
                if (Math.abs(latval - data.args['lat']) > eps || Math.abs(lonval - data.args['lon']) > eps){
                    console.warn('WARNING: lat and lon are not the same as the ones in the event', latval, lonval, data.args['lat'], data.args['lon']);
                }
                else{
                    console.log('RENDER_EVENT: lat and lon are the same as the ones in the event');
                }
            }
            Streamlit.setFrameHeight(1000);
        })

        Streamlit.setComponentReady();
        Streamlit.setFrameHeight(1000);
    }
        
