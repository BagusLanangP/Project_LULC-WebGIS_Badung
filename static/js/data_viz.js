// Fungsi menentukan warna berdasarkan kelas LULC
function getStyle(feature) {
  let kelas = feature.properties.kelas;
  let color = "#808080"; // Default Abu-abu

  if (kelas === "Badan Air") color = "#0000FF"; // Biru
  if (kelas === "Lahan Terbangun") color = "#FF0000"; // Merah
  if (kelas === "Lahan Terbuka") color = "#b28acf"; // Merah
  if (kelas === "Lahan Sawah") color = "#FFA500"; // Oranye
  if (kelas === "Lahan Vegetasi lainnya") color = "#228B22"; // Hijau

  return {
    fillColor: color,
    weight: 0.5,
    opacity: 1,
    color: "white",
    fillOpacity: 0.7,
  };
}

// // Fungsi memanggil data dari API Flask
// function loadLayer(year) {
//     fetch(`/api/geojson/${year}`)
//         .then(response => response.json())
//         .then(data => {
//             L.geoJson(data, {
//                 style: getStyle,
//                 onEachFeature: function (feature, layer) {
//                     layer.bindPopup(`<b>Kecamatan:</b> ${feature.properties.kecamatan}<br><b>Kelas:</b> ${feature.properties.kelas}`);
//                 }
//             }).addTo(map);
//         });
// }

// function getStyle(feature) {
//     // Sesuaikan dengan kolom 'Kelas_Lahan' di CSV/GeoJSON Abang
//     let kelas = feature.properties.Kelas_Lahan || feature.properties.kelas;
//     let color = "#808080";

//     if (kelas === 'Lahan Terbangun') color = "#ef4444"; // Merah
//     if (kelas === 'Lahan Sawah') color = "#f59e0b";     // Oranye
//     if (kelas === 'Lahan Vegetasi Lainnya') color = "#22c55e"; // Hijau
//     if (kelas === 'Badan Air') color = "#3b82f6";      // Biru
//     if (kelas === 'Lahan Terbuka') color = "#a8a29e";  // Abu-abu coklat

//     return { fillColor: color, weight: 0.5, opacity: 1, color: 'white', fillOpacity: 0.7 };
// }

// // Jalankan fungsi untuk tahun 2030 saat pertama load
// loadLayer('2015');
