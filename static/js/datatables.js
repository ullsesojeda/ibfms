
$(document).ready(function () {

    // =====================================================
    // IDIOMA ESPAÑOL
    // =====================================================

    const idiomaEspanol = {
        url: "https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
    };

    // =====================================================
    // ORDEN CRONOLÓGICO DE FECHAS DD/MM/AAAA
    // =====================================================

    function convertirFecha(valor) {
        if (!valor) return "";

        const texto = $("<div>").html(String(valor)).text().trim();
        const partes = texto.split("/");

        if (partes.length !== 3) return "";

        const dia = parseInt(partes[0], 10);
        const mes = parseInt(partes[1], 10);
        const anio = parseInt(partes[2], 10);

        if (
            !Number.isInteger(dia) ||
            !Number.isInteger(mes) ||
            !Number.isInteger(anio) ||
            dia < 1 || dia > 31 ||
            mes < 1 || mes > 12 ||
            anio < 1
        ) {
            return "";
        }

        return String(anio).padStart(4, "0") +
               String(mes).padStart(2, "0") +
               String(dia).padStart(2, "0");
    }

    // Tipo personalizado para ordenar fechas
    $.fn.dataTable.ext.type.order["fecha-es-pre"] = function (valor) {
        return convertirFecha(valor) || "00000000";
    };

    // Detectar fechas en encabezados que se llamen Fecha
    $.fn.dataTable.ext.type.detect.unshift(function (valor) {
        if (typeof valor !== "string") return null;

        const texto = $("<div>").html(valor).text().trim();

        if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(texto)) {
            return convertirFecha(texto) ? "fecha-es" : null;
        }

        return null;
    });

    // =====================================================
    // TABLAS CON DATATABLES
    // =====================================================

    const tablas = [
        "#tablaVisitantes",
        "#tablaEmpleados",
        "#tablaBitacora",
        "#tablaIncidentes",
        "#tablaActividades",
        "#tablaVIP",
        "#tablaUsuarios",
        "#tablaControlVehiculos"
    ];

    // =====================================================
    // BARRA HORIZONTAL SUPERIOR SINCRONIZADA
    // =====================================================

    function instalarBarraSuperior(zona) {

        if (!zona) return;

        const cuerpo = zona.querySelector(".dataTables_scrollBody");
        const encabezado = zona.querySelector(".dataTables_scrollHead");

        if (!cuerpo || !encabezado) return;

        const barras = zona.querySelectorAll(
            ":scope > .barra-scroll-superior"
        );

        for (let i = 1; i < barras.length; i++) {
            barras[i].remove();
        }

        let barra = zona.querySelector(
            ":scope > .barra-scroll-superior"
        );

        if (!barra) {

            barra = document.createElement("div");
            barra.className = "barra-scroll-superior";

            const interior = document.createElement("div");
            interior.className = "barra-scroll-interior";

            barra.appendChild(interior);
            zona.insertBefore(barra, encabezado);

            let sincronizando = false;

            barra.addEventListener("scroll", function () {
                if (sincronizando) return;

                sincronizando = true;
                cuerpo.scrollLeft = barra.scrollLeft;
                sincronizando = false;
            });

            cuerpo.addEventListener("scroll", function () {
                if (sincronizando) return;

                sincronizando = true;
                barra.scrollLeft = cuerpo.scrollLeft;
                sincronizando = false;
            });
        }

        const interior = barra.firstElementChild;

        function actualizar() {

            interior.style.width = cuerpo.scrollWidth + "px";

            barra.style.display =
                cuerpo.scrollWidth > cuerpo.clientWidth + 2
                    ? "block"
                    : "none";

            barra.scrollLeft = cuerpo.scrollLeft;
        }

        actualizar();

        if (barra._observador) {
            barra._observador.disconnect();
        }

        if ("ResizeObserver" in window) {

            barra._observador = new ResizeObserver(actualizar);
            barra._observador.observe(cuerpo);

            if (cuerpo.firstElementChild) {
                barra._observador.observe(cuerpo.firstElementChild);
            }
        }
    }

    // =====================================================
    // INICIALIZAR CADA TABLA
    // =====================================================

    tablas.forEach(function (selector) {

        const tabla = $(selector);

        if (!tabla.length) return;

        if ($.fn.DataTable.isDataTable(selector)) {
            return;
        }

        tabla.DataTable({

            responsive: false,
            scrollX: true,
            autoWidth: false,

            pageLength: 10,

            lengthMenu: [
                [10, 25, 50, 100, -1],
                [10, 25, 50, 100, "Todos"]
            ],

            language: idiomaEspanol,

            initComplete: function () {

    const api = this.api();
    const contenedor = api.table().container();

    const envoltura = contenedor.closest(".table-responsive");

    if (envoltura) {
        envoltura.dataset.scrollManaged = "true";
    }

    instalarBarraSuperior(
        contenedor.querySelector(".dataTables_scroll")
    );

    api.columns.adjust();
},
            drawCallback: function () {

                instalarBarraSuperior(
                    this.api()
                        .table()
                        .container()
                        .querySelector(".dataTables_scroll")
                );
            }
        });

    });

    // =====================================================
    // TABLAS NORMALES, SIN DATATABLES
    // =====================================================

    document.querySelectorAll(".table-responsive").forEach(
        function (contenedor) {

            if (
                contenedor.dataset.scrollManaged === "true" ||
                contenedor.querySelector(".dataTables_wrapper") ||
                contenedor.querySelector(
                    "#tablaVisitantes, #tablaEmpleados, #tablaBitacora, " +
                    "#tablaIncidentes, #tablaActividades, #tablaVIP, " +
                    "#tablaUsuarios, #tablaControlVehiculos"
                )
            ) {
                return;
            }

            const tabla = contenedor.querySelector("table");

            if (
                !tabla ||
                contenedor.dataset.topScrollReady === "true"
            ) {
                return;
            }

            contenedor.dataset.topScrollReady = "true";

            const barra = document.createElement("div");
            barra.className = "barra-scroll-superior";

            const interior = document.createElement("div");
            interior.className = "barra-scroll-interior";

            barra.appendChild(interior);

            contenedor.parentNode.insertBefore(barra, contenedor);

            let sincronizando = false;

            barra.addEventListener("scroll", function () {

                if (sincronizando) return;

                sincronizando = true;
                contenedor.scrollLeft = barra.scrollLeft;
                sincronizando = false;
            });

            contenedor.addEventListener("scroll", function () {

                if (sincronizando) return;

                sincronizando = true;
                barra.scrollLeft = contenedor.scrollLeft;
                sincronizando = false;
            });

            function actualizar() {

                interior.style.width = tabla.scrollWidth + "px";

                barra.style.display =
                    tabla.scrollWidth > contenedor.clientWidth + 2
                        ? "block"
                        : "none";

                barra.scrollLeft = contenedor.scrollLeft;
            }

            actualizar();

            if ("ResizeObserver" in window) {

                const observador = new ResizeObserver(actualizar);

                observador.observe(contenedor);
                observador.observe(tabla);
            }
        }
    );

});
