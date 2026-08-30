/*=========================================================
    IBFMS 2.0
=========================================================*/


//=========================================================
// FECHA Y HORA
//=========================================================

function actualizarHora() {

    const ahora = new Date();

    const fecha = document.getElementById("fecha");
    const hora = document.getElementById("hora");

    if (fecha) {

        fecha.innerHTML = ahora.toLocaleDateString(
            "es-MX"
        );

    }

    if (hora) {

        hora.innerHTML = ahora.toLocaleTimeString(
            "es-MX"
        );

    }

}

setInterval(actualizarHora,1000);

actualizarHora();


//=========================================================
// MODO OSCURO
//=========================================================

const modoOscuro =
document.getElementById("modoOscuro");

if(modoOscuro){

    if(localStorage.getItem("tema")=="oscuro"){

        document.body.classList.add("dark-mode");

        modoOscuro.checked=true;

    }

    modoOscuro.addEventListener(
        "change",
        function(){

            if(this.checked){

                document.body.classList.add(
                    "dark-mode"
                );

                localStorage.setItem(
                    "tema",
                    "oscuro"
                );

            }else{

                document.body.classList.remove(
                    "dark-mode"
                );

                localStorage.setItem(
                    "tema",
                    "claro"
                );

            }

        }

    );

}


//=========================================================
// MENU LATERAL
//=========================================================

const btnMenu =
document.getElementById("btnMenu");

const sidebar =
document.getElementById("sidebar");

const main =
document.querySelector(".main");


if(btnMenu && sidebar){

    btnMenu.addEventListener(
        "click",
        function(){

            if(window.innerWidth <= 768){

                sidebar.classList.toggle(
                    "mostrar"
                );

            }else{

                sidebar.classList.toggle(
                    "oculto"
                );

                main.classList.toggle(
                    "expandido"
                );

            }

        }
    );

}


//=========================================================
// RESPONSIVE
//=========================================================

window.addEventListener(
    "resize",
    function(){

        if(window.innerWidth > 768){

            sidebar.classList.remove(
                "mostrar"
            );

        }

    }

);


//=========================================================
// CERRAR MENU EN CELULAR
//=========================================================

document.addEventListener(
    "click",
    function(e){

        if(window.innerWidth <=768){

            if(
                !sidebar.contains(e.target)
                &&
                !btnMenu.contains(e.target)
            ){

                sidebar.classList.remove(
                    "mostrar"
                );

            }

        }

    }

);