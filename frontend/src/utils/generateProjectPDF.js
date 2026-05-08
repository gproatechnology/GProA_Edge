import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

/**
 * Genera un reporte PDF profesional del proyecto
 * @param {Object} project - Datos del proyecto
 * @param {Array} files - Lista de archivos
 * @param {Object} status - Estado EDGE y ahorros
 */
export const generateProjectPDF = (project, files, status) => {
  try {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    
    // Colores corporativos (basados en el tema)
    const primaryColor = [99, 102, 241]; // Indigo 500
    const darkColor = [31, 41, 55]; // Gray 800
    
    // -- CABECERA --
    doc.setFillColor(99, 102, 241);
    doc.rect(0, 0, pageWidth, 40, 'F');
    
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22);
    doc.setFont('helvetica', 'bold');
    doc.text('GProA EDGE - Reporte de Proyecto', 20, 25);
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(`Generado el: ${new Date().toLocaleString()}`, 20, 32);

    // -- INFORMACIÓN GENERAL --
    doc.setTextColor(31, 41, 55);
    doc.setFontSize(16);
    doc.text('Información General', 20, 55);
    
    autoTable(doc, {
      startY: 60,
      head: [['Campo', 'Valor']],
      body: [
        ['Proyecto', project.name || 'Sin nombre'],
        ['Tipología', project.typology || 'Sin definir'],
        ['Prioridad', project.priority || 'Baja'],
        ['Archivos Totales', String(project.file_count || 0)],
        ['Archivos Procesados', String(project.processed_count || 0)],
      ],
      theme: 'striped',
      headStyles: { fillColor: primaryColor },
      margin: { left: 20, right: 20 }
    });

    // -- AHORROS ESTIMADOS --
    let finalY = (doc.lastAutoTable && doc.lastAutoTable.finalY) ? doc.lastAutoTable.finalY : 60;
    doc.setFontSize(16);
    doc.setTextColor(31, 41, 55);
    doc.text('Ahorros Estimados EDGE', 20, finalY + 15);

    const savings = status?.savings || { energy: 0, water: 0, materials: 0 };
    autoTable(doc, {
      startY: finalY + 20,
      head: [['Categoría', 'Porcentaje de Ahorro']],
      body: [
        ['Energía', `${savings.energy}%`],
        ['Agua', `${savings.water}%`],
        ['Materiales', `${savings.materials}%`],
      ],
      theme: 'grid',
      headStyles: { fillColor: [59, 130, 246] },
      margin: { left: 20, right: 20 }
    });

    // -- ALERTAS / FALTANTES --
    finalY = (doc.lastAutoTable && doc.lastAutoTable.finalY) ? doc.lastAutoTable.finalY : finalY + 40;
    
    if (status?.faltantes && status.faltantes.length > 0) {
      doc.setFontSize(16);
      doc.setTextColor(239, 68, 68);
      doc.text('Alertas de Certificación', 20, finalY + 15);
      
      const faltantesBody = status.faltantes.map(f => [
        f.medida,
        Array.isArray(f.faltan) ? f.faltan.join(', ').replace(/_/g, ' ') : f.faltan
      ]);

      autoTable(doc, {
        startY: finalY + 20,
        head: [['Medida', 'Documentos Faltantes']],
        body: faltantesBody,
        theme: 'striped',
        headStyles: { fillColor: [239, 68, 68] },
        margin: { left: 20, right: 20 }
      });
      finalY = doc.lastAutoTable.finalY;
    } else {
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(12);
      doc.setTextColor(16, 185, 129);
      doc.text('Confirmado: Documentacion completa para certificacion', 20, finalY + 15);
      finalY = finalY + 20;
    }

    // -- LISTADO DE ARCHIVOS --
    if (finalY > 220) { doc.addPage(); finalY = 20; } else { finalY += 15; }
    
    doc.setTextColor(31, 41, 55);
    doc.setFontSize(16);
    doc.text('Detalle de Archivos', 20, finalY);
    
    const filesBody = (files || []).map(f => [
      f.filename || 'S/N',
      f.status === 'processed' ? 'Procesado' : 'Pendiente',
      f.category_edge || '-',
      f.measure_edge || '-'
    ]);

    autoTable(doc, {
      startY: finalY + 5,
      head: [['Nombre', 'Estado', 'Categoría', 'Medida']],
      body: filesBody,
      theme: 'striped',
      headStyles: { fillColor: [75, 85, 99] },
      styles: { fontSize: 8 },
      margin: { left: 20, right: 20 }
    });

    // Pie de página
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text(`Página ${i} de ${pageCount} - GProA EOSIS EDGE`, pageWidth / 2, doc.internal.pageSize.getHeight() - 10, { align: 'center' });
    }

    doc.save(`Reporte_${(project.name || 'Proyecto').replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`);
  } catch (error) {
    console.error("Critical error in generateProjectPDF:", error);
    throw error;
  }
};

