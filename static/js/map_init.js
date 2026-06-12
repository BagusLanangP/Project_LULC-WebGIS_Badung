// Inisialisasi Peta Badung
var map = L.map('map').setView([-8.55, 115.18], 11);

// Gunakan Basemap yang bersih (CartoDB Positron)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
}).addTo(map);

L.control.scale({
    imperial: false,
    metric: true,
    position: 'bottomleft'
}).addTo(map);