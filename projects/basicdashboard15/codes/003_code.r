/**
 * Belirtilen HTML canvas elementi üzerine bir dikey çubuk grafik oluşturur.
 *
 * @param {string} canvasId - Grafiğin çizileceği HTML canvas elementinin ID'si.
 * @param {object} chartData - Grafik verilerini içeren nesne. Format:
 *   {
 *     "labels": ["Ocak", "Subat", "Mart", "Nisan", "Mayis", "Haziran"],
 *     "datasets": [
 *       {
 *         "label": "Satışlar",
 *         "data": [12, 19, 3, 5, 2, 3],
 *         "backgroundColor": "rgba(75, 192, 192, 0.6)",
 *         "borderColor": "rgba(75, 192, 192, 1)",
 *         "borderWidth": 1
 *       }
 *     ]
 *   }
 * @param {object} [chartOptions] - Chart.js özelleştirme seçeneklerini içeren nesne (opsiyonel).
 * @returns {Chart|null} Oluşturulan Chart.js grafik nesnesi veya hata durumunda null.
 */
function setupBarChart(canvasId, chartData, chartOptions) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) {
    console.error(`Canvas element with ID '${canvasId}' not found.`);
    return null;
  }

  // Varsayılan seçenekler, eğer belirtilmemişse
  const defaultOptions = {
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  // Kullanıcı tarafından sağlanan seçenekleri varsayılanlarla birleştir
  const finalOptions = {
    ...defaultOptions,
    ...chartOptions
  };

  try {
    const myChart = new Chart(ctx, {
      type: 'bar',
      data: chartData,
      options: finalOptions
    });
    return myChart;
  } catch (error) {
    console.error('Error creating chart:', error);
    return null;
  }
}

// Not: Bu kodun çalışması için Chart.js kütüphanesinin HTML'e dahil edilmesi gerekmektedir.
// Örneğin, <script src="https://cdn.jsdelivr.net/npm/chart.js"></script> şeklinde.
// Ayrıca, grafiğin çizileceği <canvas id="myCanvas"></canvas> elementi HTML'de bulunmalıdır.
