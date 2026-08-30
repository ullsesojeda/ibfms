$(document).ready(function(){

    if($("#tablaVisitantes").length){

        $("#tablaVisitantes").DataTable({

            responsive: false,

            scrollX: true,

            autoWidth: false,

            pageLength: 10,

            language:{
                url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
            }

        });

    }

});
    }

});
if($("#tablaEmpleados").length){

    $("#tablaEmpleados").DataTable({

        responsive:true,

        pageLength:10,

        lengthMenu:[
            [10,25,50,100,-1],
            [10,25,50,100,"Todos"]
        ],

        language:{
            url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
        }

    });

}
if($("#tablaBitacora").length){

    $("#tablaBitacora").DataTable({

        responsive:true,

        pageLength:10,

        lengthMenu:[
            [10,25,50,100,-1],
            [10,25,50,100,"Todos"]
        ],

        language:{
            url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
        }

    });

}
if($("#tablaIncidentes").length){

    $("#tablaIncidentes").DataTable({

        responsive:true,

        pageLength:10,

        lengthMenu:[
            [10,25,50,100,-1],
            [10,25,50,100,"Todos"]
        ],

        language:{
            url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
        }

    });

}
if($("#tablaActividades").length){

    $("#tablaActividades").DataTable({

        responsive:true,

        pageLength:10,

        lengthMenu:[
            [10,25,50,100,-1],
            [10,25,50,100,"Todos"]
        ],

        language:{
            url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
        }

    });

}
if($("#tablaVIP").length){

    $("#tablaVIP").DataTable({

        responsive:true,

        pageLength:10,

        lengthMenu:[
            [10,25,50,100,-1],
            [10,25,50,100,"Todos"]
        ],

        language:{
            url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
        }

    });

}
if($("#tablaUsuarios").length){

    $("#tablaUsuarios").DataTable({

        responsive:true,

        pageLength:10,

        lengthMenu:[
            [10,25,50,100,-1],
            [10,25,50,100,"Todos"]
        ],

        language:{
            url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
        }

    });

}
if($("#tablaControlVehiculos").length){

    $("#tablaControlVehiculos").DataTable({

        responsive:true,

        pageLength:10,

        lengthMenu:[
            [10,25,50,100,-1],
            [10,25,50,100,"Todos"]
        ],

        language:{
            url:"https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
        }

    });

}