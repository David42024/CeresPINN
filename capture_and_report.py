import os
import time
from playwright.sync_api import sync_playwright
from docx import Document
from docx.shared import Inches

def create_report():
    modules = [
        "1. Dashboard General",
        "2. Análisis de Datos (EDA)",
        "3. Limpieza de Datos",
        "4. Entrenamiento",
        "5. Selección del mejor modelo",
        "6. Validación Cruzada",
        "7. Pruebas Estadísticas",
        "8. Evaluación del Modelo",
        "9. Explicabilidad del Modelo",
        "10. Distribución Geoespacial",
        "11. Reportes"
    ]

    # Content structure with CRISP-DM
    descriptions = {
        "1. Dashboard General": (
            "Fase: Comprensión del Negocio (Business Understanding)\n"
            "El dashboard general ofrece una visión global del problema, permitiendo la interacción inicial con los datos históricos de rendimiento y variables climáticas. "
            "Las métricas expuestas brindan explicabilidad sobre la exactitud y los resultados del modelo, facilitando que partes interesadas (stakeholders) no técnicas "
            "comprendan el desempeño sin entrar en detalles matemáticos complejos. Las tablas resumen los principales hallazgos experimentales de manera interpretable."
        ),
        "2. Análisis de Datos (EDA)": (
            "Fase CRISP-DM: Análisis Exploratorio de Datos (1. EDA - Data Understanding)\n"
            "Este módulo examina la calidad y distribución de los datos originales. Incluye visualizaciones descriptivas, "
            "histogramas y matrices de correlación climática. La interpretabilidad se logra visualizando relaciones directas entre "
            "variables climáticas y rendimientos agrícolas, evidenciando correlaciones fuertes y señalando anomalías que podrían afectar a los modelos futuros. Las gráficas exploratorias son autodescriptivas para facilitar la explicabilidad."
        ),
        "3. Limpieza de Datos": (
            "Fase CRISP-DM: Preparación de Datos (Data Preparation)\n"
            "Se aplican técnicas rigurosas para tratar valores nulos, duplicados y outliers temporales, sin comprometer las particiones de evaluación. "
            "La explicabilidad de la limpieza se garantiza mostrando métricas transparentes sobre filas retenidas y eliminadas, haciendo que las decisiones tomadas sobre los datos sean justificables."
        ),
        "4. Entrenamiento": (
            "Fase CRISP-DM: Modelado (2. ENTRENAMIENTOS)\n"
            "Ajuste de modelos predictivos que incluyen redes PyTorch (Physics-Informed Neural Networks) con regularizaciones basadas en derivadas. "
            "Se busca capturar la relación climática conservando la coherencia agronómica. Las gráficas de pérdida (loss) facilitan "
            "la interpretabilidad del proceso de aprendizaje y convergencia, mostrando si el modelo efectivamente aprende con cada época."
        ),
        "5. Selección del mejor modelo": (
            "Fase CRISP-DM: Modelado (3. SELECCIONAR EL MEJOR MODELO)\n"
            "Permite comparar métricas de distintos algoritmos (Ridge, Random Forest, HistGradientBoosting, MLP) para elegir el más adecuado. "
            "La interpretabilidad es clave: la selección no se basa en una caja negra, sino en comparativas transparentes y métricas estandarizadas como RMSE, MAE y R² en conjuntos de prueba independientes."
        ),
        "6. Validación Cruzada": (
            "Fase CRISP-DM: Evaluación (4. VALIDACIÓN CRUZADA)\n"
            "Implementa particiones temporales o espaciales rigurosas para evaluar la capacidad de generalización del modelo en años futuros o regiones no vistas. "
            "Evita el sobreajuste (overfitting) y provee reportes visuales robustos (boxplots) sobre la varianza de los modelos para una alta explicabilidad del comportamiento empírico."
        ),
        "7. Pruebas Estadísticas": (
            "Fase CRISP-DM: Evaluación (5. PRUEBAS ESTADÍSTICAS RIGUROSAS)\n"
            "Realiza pruebas como bootstrap por condados, pruebas de normalidad (KS), y ajustes de Holm. "
            "Ofrece un rigor estadístico exhaustivo para asegurar que las diferencias en desempeño no sean producto del azar. "
            "La explicabilidad estadística brinda confianza comprobada, presentando intervalos de confianza y valores P debidamente ajustados."
        ),
        "8. Evaluación del Modelo": (
            "Fase CRISP-DM: Evaluación (Evaluation)\n"
            "Una vez seleccionado el modelo, se exponen los metadatos del checkpoint de producción y se asegura la trazabilidad. "
            "Las tablas proveen métricas de desempeño detalladas para entender y explicar en qué condiciones el modelo se equivoca."
        ),
        "9. Explicabilidad del Modelo": (
            "Fase CRISP-DM: Evaluación (Model Explainability)\n"
            "Se emplea Inteligencia Artificial Explicable (XAI) mediante Feature Importance de Random Forest y curvas de dependencia parcial (PDP). "
            "Esto abre la 'caja negra', permitiendo entender a través de visualizaciones altamente interpretables qué factores climáticos puntuales (ej. anomalías térmicas) impulsan las predicciones del rendimiento."
        ),
        "10. Distribución Geoespacial": (
            "Fase CRISP-DM: Evaluación (Geospatial Analysis)\n"
            "Muestra mapas coropléticos interactivos. La interpretabilidad espacial es crucial en agricultura para observar "
            "cómo las variables climáticas impactan diferencialmente a nivel local, explicando la varianza que no puede ser modelada solo en el tiempo."
        ),
        "11. Reportes": (
            "Fase CRISP-DM: Despliegue (6. REPORTES)\n"
            "Generación de reportes unificados de todos los hallazgos experimentales listos para compartir con actores clave. Constituye un componente crítico de CRISP-DM, documentando explícitamente y con métricas transparentes el desempeño del modelo para la mejor toma de decisiones."
        ),
    }

    doc = Document()
    doc.add_heading('Reporte CeresPINN - ML Lab (Metodología CRISP-DM)', 0)
    doc.add_paragraph('Este documento presenta capturas de pantalla de los módulos del laboratorio de Machine Learning de CeresPINN, '
                      'estructurados con la metodología CRISP-DM. En cada sección se detalla la interpretabilidad y explicabilidad '
                      'de las figuras, tablas y gráficas generadas.')

    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Connect to the Streamlit app
        page.goto("http://localhost:8501")
        try:
            page.wait_for_selector("text=Dashboard General", timeout=20000)
        except Exception as e:
            print(f"Error esperando a que cargue Streamlit: {e}")
            browser.close()
            return

        for module in modules:
            print(f"Capturando {module}...")
            
            # Some options might have an ellipsis if cut off, but playwright's text matching 
            # uses the textcontent which is usually whole. We can match using regex or exact text.
            # Using 'has-text' and the module name. Wait for label.
            try:
                # We want to select the radio button. We can click its label.
                page.locator(f"label:has-text('{module}')").click()
                
                # Sleep to let streamlit compute and render animations/plotly charts.
                # Since EDA or geo maps take a few seconds to load.
                time.sleep(5.0)
                
                # Check for any "Running" element that Streamlit shows in the top right to wait until it finishes
                # Try waiting for the 'stStatusWidget' to detach or hide if present, but time.sleep(5) is often safer
                time.sleep(2.0)
                
                screenshot_path = os.path.join(screenshots_dir, f"{module.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}.png")
                
                page.evaluate('''() => {
                    const header = document.querySelector('header');
                    if(header) header.style.display = 'none';
                    const footer = document.querySelector('footer');
                    if(footer) footer.style.display = 'none';
                }''')

                page.screenshot(path=screenshot_path, full_page=True)

                doc.add_heading(module, level=1)
                doc.add_paragraph(descriptions.get(module, "Descripción no disponible."))
                doc.add_picture(screenshot_path, width=Inches(6.0))
                if module == "11. Reportes":
                    try:
                        page.locator("button:has-text('Generar reporte')").click()
                        time.sleep(15.0)  # Wait for report to generate
                        
                        screenshot_path_generated = os.path.join(screenshots_dir, "11_Reportes_Generado.png")
                        page.evaluate('''() => {
                            const header = document.querySelector('header');
                            if(header) header.style.display = 'none';
                            const footer = document.querySelector('footer');
                            if(footer) footer.style.display = 'none';
                        }''')
                        page.screenshot(path=screenshot_path_generated, full_page=True)
                        doc.add_heading("11. Reportes (Reporte Generado)", level=2)
                        doc.add_paragraph("Muestra la visualización de los reportes listos para exportar en PDF/JSON.")
                        doc.add_picture(screenshot_path_generated, width=Inches(6.0))
                        
                        # Now download the PDF
                        with page.expect_download() as download_info:
                            page.locator("button:has-text('Descargar PDF')").first.click()
                        download = download_info.value
                        pdf_path = os.path.join(screenshots_dir, "reporte_generado.pdf")
                        download.save_as(pdf_path)
                        
                        import fitz  # PyMuPDF
                        pdf_doc = fitz.open(pdf_path)
                        doc.add_heading("Vista del Documento PDF Descargado", level=2)
                        doc.add_paragraph("A continuación se visualizan las páginas del reporte final en formato PDF tal y como el sistema lo entrega.")
                        
                        for page_num in range(min(3, len(pdf_doc))):  # render up to 3 pages
                            pdf_page = pdf_doc.load_page(page_num)
                            pix = pdf_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # high resolution
                            page_image_path = os.path.join(screenshots_dir, f"pdf_page_{page_num+1}.png")
                            pix.save(page_image_path)
                            doc.add_picture(page_image_path, width=Inches(6.0))
                            
                    except Exception as e:
                        print(f"No se pudo generar o descargar el reporte en PDF: {e}")

            except Exception as e:
                print(f"No se pudo capturar {module}: {e}")
                
        browser.close()

    output_file = "Reporte_CRISPDM_CeresPINN_v5.docx"
    doc.save(output_file)
    print(f"Reporte generado con éxito en: {output_file}")

if __name__ == "__main__":
    create_report()
