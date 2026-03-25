/**
 * Verilen verileri kullanarak dikey çubuk grafik oluşturan bir fonksiyon.
 * Varsayılan olarak Chart.js kütüphanesi kullanılır.
 *
 * @param {Array<Object>} veri - Grafikte gösterilecek verileri içeren bir dizi.
 *   Her nesne en azından bir 'etiket' (string) ve bir 'değer' (number) içermelidir.
 *   Örnek: [{ etiket: 'Ocak', deger: 150 }, { etiket: 'Subat', deger: 220 }]
 * @param {string} grafikKonteyneriId - Grafiğin çizileceği HTML elementinin ID'si.
 */
function olusturDikeyCubukGrafik(veri, grafikKonteyneriId) {
  // Grafik konteynerini DOM'dan al
  const konteyner = document.getElementById(grafikKonteyneriId);

  // Konteyner bulunamazsa veya veri yoksa işlem yapma
  if (!konteyner || !veri || veri.length === 0) {
    console.error("Grafik konteyneri bulunamadı veya geçersiz veri sağlandı.");
    return;
  }

  // Chart.js için verileri uygun formata dönüştür
  const etiketler = veri.map(item => item.etiket);
  const degerler = veri.map(item => item.deger);

  // Mevcut bir grafik varsa temizle
  // Bu, fonksiyonun tekrar tekrar çağrılması durumunda eski grafiğin üzerine yazılmasını sağlar.
  if (konteyner.chart) {
    konteyner.chart.destroy();
  }

  // Chart.js ile yeni grafik oluştur
  const ctx = konteyner.getContext('2d');
  konteyner.chart = new Chart(ctx, {
    type: 'bar', // Grafik türü: dikey çubuk
    data: {
      labels: etiketler,
      datasets: [{
        label: 'Değerler',
        data: degerler,
        backgroundColor: 'rgba(75, 192, 192, 0.6)', // Çubukların arka plan rengi
        borderColor: 'rgba(75, 192, 192, 1)', // Çubukların kenarlık rengi
        borderWidth: 1
      }]
    },
    options: {
      responsive: true, // Grafiğin kapsayıcısına duyarlı olmasını sağlar
      maintainAspectRatio: false, // Grafiğin en boy oranını korumasını engeller (yükseklik ayarı için)
      scales: {
        y: {
          beginAtZero: true // Y ekseninin sıfırdan başlamasını sağlar
        }
      }
    }
  });
}

// Örnek Kullanım (Bu kısım genellikle HTML dosyasında veya ayrı bir JS dosyasında bulunur)
/*
// HTML'de gerekli <canvas> elementi:
// <div id="grafikAlani" style="width: 600px; height: 400px;">
//   <canvas id="myChartCanvas"></canvas>
// </div>

// Chart.js kütüphanesini HTML'e eklemeyi unutmayın:
// <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

// Fonksiyonu çağırmak için:
const ornekVeri = [
  { etiket: 'Ocak', deger: 150 },
  { etiket: 'Subat', deger: 220 },
  { etiket: 'Mart', deger: 180 },
  { etiket: 'Nisan', deger: 250 }
];

// Canvas elementini Chart.js için hazırlayın
document.addEventListener('DOMContentLoaded', (event) => {
    const canvasElement = document.createElement('canvas');
    canvasElement.id = 'myChartCanvas';
    const grafikDiv = document.getElementById('grafikAlani');
    if (grafikDiv) {
        grafikDiv.appendChild(canvasElement);
        // Fonksiyonu çağır
        olusturDikeyCubukGrafik(ornekVeri, 'grafikAlani');
    } else {
        console.error("'grafikAlani' ID'li div bulunamadı.");
    }
});
*/
