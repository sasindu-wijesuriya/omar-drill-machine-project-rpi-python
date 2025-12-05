#include <Wire.h>
#include <RTClib.h>

//PINES A CONECTAR!!!!
const int pulsos1 = 12;
const int dir1 = 11;
const int pulsos2 = 10;
const int dir2 = 9;
const int btnReset = 22;  //AHORA BOTON HOME
const int btnStart = 23;
const int btnStop = 24;
const int btnTala = 25;
const int switchS = 5;
const int finInit = 4;  //ESTE YA NO EXISTE
const int finHome = 3;  //AHORA HOME ES EL INICIO
const int finFinal = 2;
const int joystick = A0;

//VARIABLES A CAMBIAR------------------------------------------------------------------------------

//VELOCIDAD TALADRO CICLO 2
int velocidadPasosTaladroCiclo2 = 2640; //2200

//VARIABLE PASOS TALADRO SEGUNDO CICLO 2
int pasosTaladroCiclo2 = 200;//200

//CANTIDAD DE GIROS TALADRO CICLO 2
int cantidadGirosTaladroCiclo2 = 3;

//PASOS POR VUELTA TALADRO
int pasosPorVueltaTaladro = 400;//400

//CANTIDAD DE VUELTAS NIVEL 1
float cantidadPrimerNivel1 = 100;//100
float cantidadPrimerNivel2 = 400;
float cantidadPrimerNivel3 = 500;
float cantidadPrimerNivel4 = 400;
float cantidadPrimerNivel5 = 50;

//CANTIDAD DE VUELTAS NIVEL 2
float cantidadSegundoNivel1 = 1000; //1000
float cantidadSegundoNivel2 = 800;
float cantidadSegundoNivel3 = 1000;
float cantidadSegundoNivel4 = 800;
float cantidadSegundoNivel5 = 20;

int tiempoAntesDeGirar = 2000;  //ESTE TIEMPO ESTA DADO EN MILISEGUNDOS!!!!!!!!!!

int velocidadLineal1 = 3900;  //Numero entre 500 o 3500 dependiendo de las pruebas 3000
int velocidadLineal2 = 7000;  //Numero entre 500 o 3500 dependiendo de las pruebas
int velocidadLineal3 = 3200;  //Numero entre 500 o 3500 dependiendo de las pruebas
int velocidadLineal4 = 3200;  //Numero entre 500 o 3500 dependiendo de las pruebas
int velocidadLineal5 = 7000;  //Numero entre 500 o 3500 dependiendo de las pruebas     9000=7/14.16 10.16

int velocidadTaladro1 = 2860;  //Numero entre 500 o 3500 dependiendo de las pruebas /2200
int velocidadTaladro2 = 2200;  //Numero entre 500 o 3500 dependiendo de las pruebas
int velocidadTaladro3 = 2200;  //Numero entre 500 o 3500 dependiendo de las pruebas
int velocidadTaladro4 = 2200;  //Numero entre 500 o 3500 dependiendo de las pruebas
int velocidadTaladro5 = 2200;  //Numero entre 500 o 3500 dependiendo de las pruebas

int velocidadLinealHome = 4000;  //Numero entre 500 o 3500 dependiendo de las pruebas
int velocidadTaladro = 2200;     //Numero entre 500 o 3500 dependiendo de las pruebas

int limiteInferiorVelocidad = 1500;  //La más rapida MODO MANUAL!!!!!
int limiteSuperiorVelocidad = 2500;  //La más lenta MODO MANUAL!!!!!

//IMPORTANTE!!! CAMBIAR PARA CAMBIAR LA LOGICA DE LOS GIROS DEL MOTOR LINEAL
boolean sentidoGiroLineal = 1;
boolean sentidoGiroTaladro = 0;  //Cambiar 0 por 1 o 1 por 0 para el sentido del giro
boolean sentidoCiclos = 0;

int tiempoParaEmpezarDespuesDeStop = 2000;  //Esta en milisegundos tiempos de pausa

//CANTIDADES DE PASOS
//CANTIDAD DE PASOS DESPUES DE HOME
int pasosDespuesHome = 425;  // pasos que tiene que avanzar para ir despues de home 375-425
//CANTIDAD DE PASOS PRIMER NIVEL
int cantidadPasosPrimerNivel1 = 175;//175
int cantidadPasosPrimerNivel2 = 380;
int cantidadPasosPrimerNivel3 = 380;
int cantidadPasosPrimerNivel4 = 380;
int cantidadPasosPrimerNivel5 = 380;
//CANTIDAD DE PASOS DESPUES DE HOME
int pasosAcomodoParaSegundoNivel1 = 10;//175
int pasosAcomodoParaSegundoNivel2 = 305;
int pasosAcomodoParaSegundoNivel3 = 305;
int pasosAcomodoParaSegundoNivel4 = 305;
int pasosAcomodoParaSegundoNivel5 = 305;
//CANTIDAD DE PASOS SEGUNDO NIVEL
int cantidadPasosSegundoNivel1 = 390;//225
int cantidadPasosSegundoNivel2 = 80;
int cantidadPasosSegundoNivel3 = 80;
int cantidadPasosSegundoNivel4 = 80;
int cantidadPasosSegundoNivel5 = 80;
//-------------------------------------------------------------------------------------------------AQUI TERMINAN LAS VARIABLES A CAMBIAR

boolean btnResetPasado = 0;
boolean btnStartPasado = 0;
boolean btnStopPasado = 0;
boolean btnTalaPasado = 0;
boolean switchSPasado = 0;
boolean finInitPasado = 0;
boolean finHomePasado = 0;
boolean finFinalPasado = 0;
String comando = "";
boolean enEjecucion = 0;
boolean enEspera = 0;
boolean modoManual = 0;
boolean sentidoManual = 0;  //0 --> HACIA EL FINAL, 1 --> HACIA EL INICIO
int velocidadManual = 0;
boolean movimientoTaladro = 0;
boolean estadoPulsosTaladro = 0;
boolean movimientoLinealManual = 0;
boolean estadoPulsosLineal = 0;
boolean movimientoLinealAutomatico = 0;
unsigned long last = 0;
unsigned long lastTaladro = 0;
unsigned long lastLineal = 0;
unsigned long lastMovimientos = 0;
unsigned long lastSegundo = 0;
boolean bloqueoFinalInicio = 0;
boolean bloqueoFinalFinal = 0;
int pasosElegidosNivel1 = 0;
int pasosMovimientoIntermedioElegidos = 0;
int pasosElegidosNivel2 = 0;
int cantidadPrimerNivel = 0;
int cantidadSegundoNivel = 0;
int contadorRebotes = 0;
int velocidadLineal = 0;
//int velocidadTaladro = 0;
boolean resetPresionado = 0;

RTC_DS3231 rtc;
unsigned long lastSecuenciaTiempo = 0;

//-------------------------------------------------------------------------FECHA SELECCIONADA
const int yearTarget = 2027;
const int monthTarget = 10;
const int dayTarget = 13;
//-----------------------------------------------------------------------------------------Funcion para mandar mensajes a la pantalla nextion
void mostrar(String c) {
  Serial3.print(c);
  Serial3.write(0xff);
  Serial3.write(0xff);
  Serial3.write(0xff);
}

//-----------------------------------------------------------------------------------------Funcion para llegar a home
void encontrarHome() {
  Serial.println("Encontrando home");
  velocidadLineal = velocidadLinealHome;
  //CUANTO GIRA HACIA EL FIN ES CON "!", CUANDO NO GIRA HACIA EL FIN ES SIN "!"
  digitalWrite(dir1, sentidoGiroLineal);  //HACIA HOME
  while (1) {

    if (!digitalRead(switchS)) {
      motorStopSwitch();
    }

    if (micros() - lastMovimientos >= velocidadLineal) {

      lastMovimientos = micros();

      estadoPulsosLineal = !estadoPulsosLineal;

      digitalWrite(pulsos1, estadoPulsosLineal);
    }

    if (finHomePasado != digitalRead(finHome)) {
      finHomePasado = digitalRead(finHome);
      if (finHomePasado) {
        break;
      }
    }

    if (btnStopPasado != digitalRead(btnStop)) {
      btnStopPasado = digitalRead(btnStop);
      if (btnStopPasado) {
        Serial.println("BTN STOP PRESIONADO");
        motorDetenidoPorBotonStop();
      }
    }
  }

  Serial.println("Home encontrado");

  Serial.println("Moviendome pasos para acomodar despues del home");
  //CUANTO GIRA HACIA EL FIN ES CON "!", CUANDO NO GIRA HACIA EL FIN ES SIN "!"
  //PASOS QUE EL MOTOR GIRA DESPUES DE HOME PARA ACOMODARSE
  digitalWrite(dir1, !sentidoGiroLineal);
  for (int i = 0; i < pasosDespuesHome; i++) {
    digitalWrite(pulsos1, 1);
    delayMicroseconds(velocidadLineal);
    digitalWrite(pulsos1, 0);
    delayMicroseconds(velocidadLineal);
    if (btnStopPasado != digitalRead(btnStop)) {
      btnStopPasado = digitalRead(btnStop);
      if (btnStopPasado) {
        Serial.println("BTN STOP PRESIONADO");
        motorDetenidoPorBotonStop();
      }
    }
    if (!digitalRead(switchS)) {
      motorStopSwitch();
    }
  }
  Serial.println("Proceso de acomodado terminado");
  digitalWrite(pulsos1, 0);
  digitalWrite(dir1, 0);
}

//-----------------------------------------------------------------------------------------Motor detenido por boton
void motorDetenidoPorBotonStop() {

  String texto = "EN PAUSA";
  //De aqui no saldra hasta que se pulse start de nuevo

  mostrar("page3.t1.txt=\"" + texto + "\"");

  while (1) {

    if (btnStartPasado != digitalRead(btnStart)) {
      btnStartPasado = digitalRead(btnStart);

      if (btnStartPasado) {
        Serial.println("BTN START PRESIONADO");
        break;
      }
    }

    /*if (btnResetPasado != digitalRead(btnReset)) {
      btnResetPasado = digitalRead(btnReset);
      if (btnResetPasado) {
        Serial.println("RST PRES");
        mostrar("page 1");
        movimientoLinealAutomatico = 0;
        movimientoTaladro = 0;
        movimientoLinealManual = 0;
        enEjecucion = 0;
        enEspera = 0;
        contadorRebotes = 0;
        pasosElegidosNivel1 = 0;
        pasosMovimientoIntermedioElegidos = 0;
        pasosElegidosNivel2 = 0;
        cantidadPrimerNivel = 0;
        cantidadSegundoNivel = 0;
        resetPresionado = 1;
        digitalWrite(dir1, 0);
        digitalWrite(pulsos1, 0);
        digitalWrite(dir2, 0);
        digitalWrite(pulsos2, 0);
        encontrarHome();
        break;
      }
      }*/
  }

  delay(tiempoParaEmpezarDespuesDeStop);
  //mostrar("page3.t1.txt=\"" + String(contadorRebotes) + "\"");
}
//-----------------------------------------------------------------------------------------Motor detenido por boton
void motorStopSwitch() {
  String texto = "EN PAUSA";
  //De aqui no saldra hasta que se pulse start de nuevo

  mostrar("page3.t1.txt=\"" + texto + "\"");

  while (1) {

    if (btnStartPasado != digitalRead(btnStart)) {
      btnStartPasado = digitalRead(btnStart);

      if (btnStartPasado) {
        Serial.println("BTN START PRESIONADO");
        break;
      }
    }
  }

  delay(tiempoParaEmpezarDespuesDeStop);
}
//-----------------------------------------------------------------------------------------Funcion para comunicarte con la pantalla nextion
void serialNextion() {
  if (Serial3.available()) {

    char dato = Serial3.read();

    if (dato != '.') {
      comando += dato;
    } else {
      Serial.print("Comando: ");
      Serial.println(comando);


      if (!enEjecucion) {

        String textoCompleto = "CARGAR PIEZAS";  //--------------------AQUI CAMBIAR
        String txtLinea3 = "PRESIONE ARRANCAR";

        if (comando == "A") {
          encontrarHome();
          enEspera = 1;
          pasosElegidosNivel1 = cantidadPasosPrimerNivel1;
          pasosMovimientoIntermedioElegidos = pasosAcomodoParaSegundoNivel1;
          pasosElegidosNivel2 = cantidadPasosSegundoNivel1;
          cantidadPrimerNivel = cantidadPrimerNivel1;
          cantidadSegundoNivel = cantidadSegundoNivel1;
          velocidadLineal = velocidadLineal1;
          velocidadTaladro = velocidadTaladro1;
          String txtModo = "MODO 1 SELECCIONADO";
          mostrar("page2.t0.txt=\"" + textoCompleto + "\"");
          mostrar("page2.t1.txt=\"" + txtModo + "\"");
          mostrar("page2.t2.txt=\"" + txtLinea3 + "\"");
        }

        if (comando == "B") {
          encontrarHome();
          enEspera = 1;
          pasosElegidosNivel1 = cantidadPasosPrimerNivel2;
          pasosMovimientoIntermedioElegidos = pasosAcomodoParaSegundoNivel2;
          pasosElegidosNivel2 = cantidadPasosSegundoNivel2;
          cantidadPrimerNivel = cantidadPrimerNivel2;
          cantidadSegundoNivel = cantidadSegundoNivel2;
          velocidadLineal = velocidadLineal2;
          velocidadTaladro = velocidadTaladro2;
          String txtModo = "MODO 2 SELECCIONADO";
          mostrar("page2.t0.txt=\"" + textoCompleto + "\"");
          mostrar("page2.t1.txt=\"" + txtModo + "\"");
          mostrar("page2.t2.txt=\"" + txtLinea3 + "\"");
        }

        if (comando == "C") {
          encontrarHome();
          enEspera = 1;
          pasosElegidosNivel1 = cantidadPasosPrimerNivel3;
          pasosMovimientoIntermedioElegidos = pasosAcomodoParaSegundoNivel3;
          pasosElegidosNivel2 = cantidadPasosSegundoNivel3;
          cantidadPrimerNivel = cantidadPrimerNivel3;
          cantidadSegundoNivel = cantidadSegundoNivel3;
          velocidadLineal = velocidadLineal3;
          velocidadTaladro = velocidadTaladro3;
          String txtModo = "MODO 3 SELECCIONADO";
          mostrar("page2.t0.txt=\"" + textoCompleto + "\"");
          mostrar("page2.t1.txt=\"" + txtModo + "\"");
          mostrar("page2.t2.txt=\"" + txtLinea3 + "\"");
        }

        if (comando == "D") {
          encontrarHome();
          enEspera = 1;
          pasosElegidosNivel1 = cantidadPasosPrimerNivel4;
          pasosMovimientoIntermedioElegidos = pasosAcomodoParaSegundoNivel4;
          pasosElegidosNivel2 = cantidadPasosSegundoNivel4;
          cantidadPrimerNivel = cantidadPrimerNivel4;
          cantidadSegundoNivel = cantidadSegundoNivel4;
          velocidadLineal = velocidadLineal4;
          velocidadTaladro = velocidadTaladro4;
          String txtModo = "MODO 4 SELECCIONADO";
          mostrar("page2.t0.txt=\"" + textoCompleto + "\"");
          mostrar("page2.t1.txt=\"" + txtModo + "\"");
          mostrar("page2.t2.txt=\"" + txtLinea3 + "\"");
        }

        if (comando == "E") {
          encontrarHome();
          enEspera = 1;
          pasosElegidosNivel1 = cantidadPasosPrimerNivel5;
          pasosMovimientoIntermedioElegidos = pasosAcomodoParaSegundoNivel5;
          pasosElegidosNivel2 = cantidadPasosSegundoNivel5;
          cantidadPrimerNivel = cantidadPrimerNivel5;
          cantidadSegundoNivel = cantidadSegundoNivel5;
          velocidadLineal = velocidadLineal5;
          velocidadTaladro = velocidadTaladro5;
          String txtModo = "MODO 5 SELECCIONADO";
          mostrar("page2.t0.txt=\"" + textoCompleto + "\"");
          mostrar("page2.t1.txt=\"" + txtModo + "\"");
          mostrar("page2.t2.txt=\"" + txtLinea3 + "\"");
        }

        if (comando == "0") {
          movimientoTaladro = 0;
          digitalWrite(dir2, 0);
          digitalWrite(pulsos2, 0);
          movimientoLinealManual = 0;
          digitalWrite(dir1, 0);
          digitalWrite(pulsos1, 0);
          modoManual = 0;
        }

        if (comando == "1") {
          if (!enEjecucion && !enEspera) {
            modoManual = 1;
          }
        }
      }

      comando = "";
    }

    if (comando == "X") {
      enEspera = 0;
      Serial.println("Operacion cancelada");
    }
  }
}

//-----------------------------------------------------------------------------------------Funcion de movimiento de los motores
void movimientoMotores() {
  if (micros() - lastTaladro >= velocidadTaladro && movimientoTaladro) {

    lastTaladro = micros();

    estadoPulsosTaladro = !estadoPulsosTaladro;

    digitalWrite(pulsos2, estadoPulsosTaladro);
  }

  if (micros() - lastLineal >= velocidadManual && movimientoLinealManual) {

    lastLineal = micros();

    estadoPulsosLineal = !estadoPulsosLineal;

    digitalWrite(pulsos1, estadoPulsosLineal);
  }

  if (micros() - lastMovimientos >= velocidadLineal && movimientoLinealAutomatico) {

    lastMovimientos = micros();

    estadoPulsosLineal = !estadoPulsosLineal;

    digitalWrite(pulsos1, estadoPulsosLineal);
  }
}

void funcionManual() {
  if (modoManual) {
    int valorPotenciometro = analogRead(joystick);

    velocidadTaladro = velocidadTaladro;

    if (valorPotenciometro < 352) {
      if (!digitalRead(finHome)) {  // Verifica si el final de carrera home no está activado
        Serial.println("H");        // ESTO QUIERE DECIR QUE VA HACIA HOME
        movimientoLinealManual = 1;
        digitalWrite(dir1, sentidoGiroLineal);
        velocidadManual = map(valorPotenciometro, 352, 0, limiteSuperiorVelocidad, limiteInferiorVelocidad);
      } else {
        // Rebote hacia el otro lado
        Serial.println("Sensor home activado, rebotando hacia el otro lado");
        digitalWrite(dir1, !sentidoGiroLineal);
        int p = 0;
        while (1) {
          if (micros() - lastLineal >= 2500) {
            lastLineal = micros();
            estadoPulsosLineal = !estadoPulsosLineal;
            digitalWrite(pulsos1, estadoPulsosLineal);
            p++;
            if (p >= 300) {
              break;
            }
          }
        }
        movimientoLinealManual = 0;
        digitalWrite(pulsos1, 0);
      }
    } else if (valorPotenciometro > 652) {
      if (!digitalRead(finFinal)) {  // Verifica si el final de carrera final no está activado
        Serial.println("F");         // ESTO QUIERE DECIR QUE VA HACIA FINAL
        movimientoLinealManual = 1;
        digitalWrite(dir1, !sentidoGiroLineal);
        velocidadManual = map(valorPotenciometro, 652, 1023, limiteSuperiorVelocidad, limiteInferiorVelocidad);
      } else {
        // Rebote hacia el otro lado
        Serial.println("Sensor final activado, rebotando hacia el otro lado");
        digitalWrite(dir1, sentidoGiroLineal);
        int p = 0;
        while (1) {
          if (micros() - lastLineal >= 2500) {
            lastLineal = micros();
            estadoPulsosLineal = !estadoPulsosLineal;
            digitalWrite(pulsos1, estadoPulsosLineal);
            p++;
            if (p >= 300) {
              break;
            }
          }
        }
        movimientoLinealManual = 0;
        digitalWrite(pulsos1, 0);
      }
    } else {
      movimientoLinealManual = 0;
      digitalWrite(dir1, 1);
      digitalWrite(pulsos1, 0);
    }

    if (btnTalaPasado != digitalRead(btnTala)) {
      btnTalaPasado = digitalRead(btnTala);
      if (!btnTalaPasado) {
        movimientoTaladro = !movimientoTaladro;
        if (!movimientoTaladro) {
          digitalWrite(dir2, 0);
          digitalWrite(pulsos2, 0);
        }
      }
      delay(50);
    }
  }
}


void funcionAutomatico() {
  if (!modoManual) {
    if (enEspera) {
      if (digitalRead(switchS)) {
        if (btnStartPasado != digitalRead(btnStart)) {
          btnStartPasado = digitalRead(btnStart);
          Serial.println("EL BOTON START SE HA PULSADO PARA INICIAR EL PROCESO");
          if (btnStartPasado) {
            Serial.println("Inicia la funcion de ejecucion--------");
            mostrar("page 3");
            funcionEnEjecucion();
            Serial.println("Termina la funcion de ejecucion--------");
          }
        }
      }
    }
  }
}

void funcionEnEjecucion() {
  resetPresionado = 0;

  //Iniciando el tiempo de movimiento del taladro
  unsigned long tiempoParaComenzar = millis();
  while (1) {
    if (millis() - tiempoParaComenzar >= tiempoAntesDeGirar) {
      break;
    }
    if (!digitalRead(switchS)) {
      motorStopSwitch();
    }
    if (btnStopPasado != digitalRead(btnStop)) {
      btnStopPasado = digitalRead(btnStop);
      if (btnStopPasado) {
        Serial.println("BTN STOP PRESIONADO");
        motorDetenidoPorBotonStop();
      }
    }

    /*if (btnResetPasado != digitalRead(btnReset)) {
      btnResetPasado = digitalRead(btnReset);
      if (btnResetPasado) {
        Serial.println("RST PRES");
        mostrar("page 1");
        movimientoLinealAutomatico = 0;
        movimientoTaladro = 0;
        movimientoLinealManual = 0;
        enEjecucion = 0;
        enEspera = 0;
        contadorRebotes = 0;
        pasosElegidosNivel1 = 0;
        pasosMovimientoIntermedioElegidos = 0;
        pasosElegidosNivel2 = 0;
        cantidadPrimerNivel = 0;
        cantidadSegundoNivel = 0;
        resetPresionado = 1;
        digitalWrite(dir1, 0);
        digitalWrite(pulsos1, 0);
        digitalWrite(dir2, 0);
        digitalWrite(pulsos2, 0);
        encontrarHome();
        break;
      }
      }*/

    digitalWrite(pulsos2, 1);
    delayMicroseconds(velocidadTaladro);
    digitalWrite(pulsos2, 0);
    delayMicroseconds(velocidadTaladro);
  }

  Serial.println("Empezando ciclo 1");
  //Comienza el nivel 1--------------------------------------------------------------------------------------------------
  boolean haciaFinal = 1;
  int conteoPulsos = 0;
  int conteoPulsosTaladro = 0;
  int conteoVueltas = 0;
  boolean terminarMovimiento = 0;
  if (!resetPresionado) {

    while (1) {
      if (!digitalRead(switchS)) {
        motorStopSwitch();
      }

      if (btnStopPasado != digitalRead(btnStop)) {
        btnStopPasado = digitalRead(btnStop);
        if (btnStopPasado) {
          Serial.println("BTN STOP PRESIONADO");
          motorDetenidoPorBotonStop();
        }
      }

      /*if (btnResetPasado != digitalRead(btnReset)) {
        btnResetPasado = digitalRead(btnReset);
        if (btnResetPasado) {
          Serial.println("RST PRES");
          mostrar("page 1");
          movimientoLinealAutomatico = 0;
          movimientoTaladro = 0;
          movimientoLinealManual = 0;
          enEjecucion = 0;
          enEspera = 0;
          contadorRebotes = 0;
          pasosElegidosNivel1 = 0;
          pasosMovimientoIntermedioElegidos = 0;
          pasosElegidosNivel2 = 0;
          cantidadPrimerNivel = 0;
          cantidadSegundoNivel = 0;
          resetPresionado = 1;
          digitalWrite(dir1, 0);
          digitalWrite(pulsos1, 0);
          digitalWrite(dir2, 0);
          digitalWrite(pulsos2, 0);
          encontrarHome();
          break;
        }
        }*/

      //CUANTO GIRA HACIA EL FIN ES CON "!", CUANDO NO GIRA HACIA EL FIN ES SIN "!"
      if (haciaFinal) {  //Hacia final
        digitalWrite(dir1, !sentidoCiclos);
      } else {  //Hacia Home
        digitalWrite(dir1, sentidoCiclos);
      }

      if (micros() - lastTaladro >= velocidadTaladro && !terminarMovimiento) {

        lastTaladro = micros();

        estadoPulsosTaladro = !estadoPulsosTaladro;

        digitalWrite(pulsos2, estadoPulsosTaladro);

        if (estadoPulsosTaladro) {
          conteoPulsosTaladro++;
        }
      }

      if (micros() - lastMovimientos >= velocidadLineal) {

        lastMovimientos = micros();

        estadoPulsosLineal = !estadoPulsosLineal;

        digitalWrite(pulsos1, estadoPulsosLineal);

        if (estadoPulsosLineal) {
          conteoPulsos++;
          if (haciaFinal) {
            Serial.print("D: ");
          } else {
            Serial.print("I: ");
          }
          Serial.println(conteoPulsos);
        }
      }

      if (conteoPulsos >= pasosElegidosNivel1) {
        haciaFinal = !haciaFinal;
        conteoPulsos = 0;
        if (terminarMovimiento && haciaFinal) {
          terminarMovimiento = 0;
          break;
        }
      }

      if (conteoPulsosTaladro >= pasosPorVueltaTaladro) {
        conteoPulsosTaladro = 0;
        conteoVueltas++;
        mostrar("page3.t1.txt=\"" + String(conteoVueltas) + "\"");
      }

      if (conteoVueltas >= cantidadPrimerNivel) {
        conteoVueltas = 0;
        terminarMovimiento = 1;
      }
    }
  }
  delay(1000);
  Serial.println("Empezando intermedio");
  //Comienza el movimiento intermedio------------------------------------------------------------------------------------------
  //CUANTO GIRA HACIA EL FIN ES CON "!", CUANDO NO GIRA HACIA EL FIN ES SIN "!"
  //PASOS QUE EL MOTOR GIRA DESPUES DEL PRIMER NIVEL
  if (!resetPresionado) {
    conteoPulsos = 0;
    digitalWrite(dir1, sentidoCiclos);//!
    while (1) {
      //pasosMovimientoIntermedioElegidos
      if (!digitalRead(switchS)) {
        motorStopSwitch();
      }

      if (btnStopPasado != digitalRead(btnStop)) {
        btnStopPasado = digitalRead(btnStop);
        if (btnStopPasado) {
          Serial.println("BTN STOP PRESIONADO");
          motorDetenidoPorBotonStop();
        }
      }

      /*if (btnResetPasado != digitalRead(btnReset)) {
        btnResetPasado = digitalRead(btnReset);
        if (btnResetPasado) {
          Serial.println("RST PRES");
          mostrar("page 1");
          movimientoLinealAutomatico = 0;
          movimientoTaladro = 0;
          movimientoLinealManual = 0;
          enEjecucion = 0;
          enEspera = 0;
          contadorRebotes = 0;
          pasosElegidosNivel1 = 0;
          pasosMovimientoIntermedioElegidos = 0;
          pasosElegidosNivel2 = 0;
          cantidadPrimerNivel = 0;
          cantidadSegundoNivel = 0;
          resetPresionado = 1;
          digitalWrite(dir1, 0);
          digitalWrite(pulsos1, 0);
          digitalWrite(dir2, 0);
          digitalWrite(pulsos2, 0);
          encontrarHome();
          break;
        }
        }*/

      /*if (micros() - lastTaladro >= velocidadTaladro) {

        lastTaladro = micros();

        estadoPulsosTaladro = !estadoPulsosTaladro;

        digitalWrite(pulsos2, estadoPulsosTaladro);

        }*/

      if (micros() - lastMovimientos >= velocidadLineal) {

        lastMovimientos = micros();

        estadoPulsosLineal = !estadoPulsosLineal;

        digitalWrite(pulsos1, estadoPulsosLineal);

        conteoPulsos++;
      }

      if ((conteoPulsos / 2) >= pasosMovimientoIntermedioElegidos) {
        haciaFinal = !haciaFinal;
        conteoPulsos = 0;
        break;
      }
    }
  }

  delay(1000);
  Serial.println("Empezando ciclo 2");
  //Comienza el nivel 2-----------------------------------------------------------------------------------------------------------------------------
  haciaFinal = 1;
  conteoPulsos = 0;
  conteoPulsosTaladro = 0;
  conteoVueltas = 0;
  terminarMovimiento = 0;
  if (!resetPresionado) {
    while (1) {

      if (!digitalRead(switchS)) {
        motorStopSwitch();
      }

      if (btnStopPasado != digitalRead(btnStop)) {
        btnStopPasado = digitalRead(btnStop);
        if (btnStopPasado) {
          Serial.println("BTN STOP PRESIONADO");
          motorDetenidoPorBotonStop();
        }
      }

      //CUANTO GIRA HACIA EL FIN ES CON "!", CUANDO NO GIRA HACIA EL FIN ES SIN "!"
      if (haciaFinal) {  //Hacia final---------------------------------------------------------------------------------------------------------
        digitalWrite(dir1, !sentidoCiclos);
      } else {  //Hacia Home
        digitalWrite(dir1, sentidoCiclos);
      }

      if (micros() - lastMovimientos >= velocidadLineal) {

        lastMovimientos = micros();

        estadoPulsosLineal = !estadoPulsosLineal;

        digitalWrite(pulsos1, estadoPulsosLineal);
        if (estadoPulsosLineal) {
          conteoPulsos++;
          if (haciaFinal) {
            Serial.print("D: ");
          } else {
            Serial.print("I: ");
          }
          Serial.println(conteoPulsos);
        }
      }

      if (conteoPulsos >= pasosElegidosNivel2) {
        haciaFinal = !haciaFinal;
        conteoPulsos = 0;

        if (!terminarMovimiento && haciaFinal) {
          conteoVueltas++;
          for (int i = 0; i < pasosTaladroCiclo2; i++) {
            estadoPulsosTaladro = !estadoPulsosTaladro;
            digitalWrite(pulsos2, estadoPulsosTaladro);
            delayMicroseconds(velocidadPasosTaladroCiclo2);
          }
        }

        if (terminarMovimiento && haciaFinal) {
          terminarMovimiento = 0;
          mostrar("page 4");
          String textoValor1 = "ABRIR Y DESCARGUE";
          mostrar("page4.t0.txt=\"" + textoValor1 + "\"");
          String textoValor2 = "PRESIONE INICIO";
          mostrar("page4.t1.txt=\"" + textoValor2 + "\"");
          String textoValor3 = "PARA SIG. CICLO ";
          mostrar("page4.t2.txt=\"" + textoValor3 + "\"");
          break;
        }
      }

      if (conteoVueltas >= cantidadGirosTaladroCiclo2) {
        conteoVueltas = 0;
        terminarMovimiento = 1;
      }
    }
  }

  Serial.println("ESPERANDO PULSACION DE RESET");
  //FINAL ESPERANDO TERMINO DE PROCESO-------------------------------------------------------------------------------------------------------
  if (!resetPresionado) {
    int conteoVecesQueSePresionaReset = 0;
    while (conteoVecesQueSePresionaReset == 0) {
      if (digitalRead(switchS)) {
        if (btnResetPasado != digitalRead(btnReset)) {
          btnResetPasado = digitalRead(btnReset);
          if (btnResetPasado) {
            Serial.println("RST PRES");
            conteoVecesQueSePresionaReset++;
            Serial.print("Veces que se presiona reset: ");
            Serial.println(conteoVecesQueSePresionaReset);
            mostrar("page 1");
            movimientoLinealAutomatico = 0;
            movimientoTaladro = 0;
            movimientoLinealManual = 0;
            enEjecucion = 0;
            enEspera = 0;
            contadorRebotes = 0;
            pasosElegidosNivel1 = 0;
            pasosMovimientoIntermedioElegidos = 0;
            pasosElegidosNivel2 = 0;
            cantidadPrimerNivel = 0;
            cantidadSegundoNivel = 0;
            resetPresionado = 1;
            digitalWrite(dir1, 0);
            digitalWrite(pulsos1, 0);
            digitalWrite(dir2, 0);
            digitalWrite(pulsos2, 0);
            encontrarHome();
            break;
          }
        }
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial3.begin(9600);


  pinMode(pulsos1, OUTPUT);
  pinMode(dir1, OUTPUT);
  pinMode(pulsos2, OUTPUT);
  pinMode(dir2, OUTPUT);
  pinMode(finInit, INPUT);
  pinMode(finHome, INPUT);
  pinMode(finFinal, INPUT);
  pinMode(btnReset, INPUT);
  pinMode(btnStart, INPUT);
  pinMode(btnStop, INPUT);
  pinMode(btnTala, INPUT);
  pinMode(switchS, INPUT);
  pinMode(joystick, INPUT);

  // Verificar si el RTC está presente
  if (!rtc.begin()) {
    Serial.println("No se encuentra el RTC");
    while (true)
      ;  // Entra en bucle infinito si no se encuentra el RTC
  }

  // Verificar si el RTC perdió energía (batería agotada)
  if (rtc.lostPower()) {
    Serial.println("RTC perdió energía, reseteando la fecha y hora...");
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));  // Ajustar a la fecha y hora de compilación
    while (true)
      ;  // Entra en bucle infinito si el RTC perdió energía
  }

  // Aquí puedes establecer la fecha y hora manualmente si lo necesitas
  // rtc.adjust(DateTime(2024, 8, 13, 0, 0, 0)); // AAAA, MM, DD, HH, MM, SS


  digitalWrite(dir2, sentidoGiroTaladro);

  if (!digitalRead(switchS)) {
    motorStopSwitch();
  }

  encontrarHome();
  //DELAY TIEMPO SPLASH SCREEN
  delay(3000);
  mostrar("page 1");
  Serial.println("page 1");
}

void loop() {

  if (millis() - lastSecuenciaTiempo >= 1000) {
    lastSecuenciaTiempo = millis();

    DateTime now = rtc.now();

    // Mostrar la fecha y hora actual en una sola línea
    Serial.println(String(now.year()) + '/' + String(now.month()) + '/' + String(now.day()) + ' ' + String(now.hour()) + ':' + String(now.minute()) + ':' + String(now.second()));

    // Verificar si se ha alcanzado la fecha objetivo
    if (now.year() >= yearTarget && now.month() >= monthTarget && now.day() >= dayTarget) {
      Serial.println("¡Fecha objetivo alcanzada! Entrando en bucle infinito...");
      while (true)
        ;  // Entra en bucle infinito si se ha alcanzado la fecha objetivo
    }

    // Verificar si el RTC no funciona correctamente (fecha muy antigua)
    if (now.year() < 2000) {
      Serial.println("Error en el RTC: Fecha no válida. Entrando en bucle infinito...");
      while (true)
        ;  // Entra en bucle infinito si el RTC devuelve una fecha no válida
    }
  }

  if (btnResetPasado != digitalRead(btnReset)) {
    btnResetPasado = digitalRead(btnReset);
    if (btnResetPasado) {
      Serial.println("RST PRES");
      mostrar("page 1");
      movimientoLinealAutomatico = 0;
      movimientoTaladro = 0;
      movimientoLinealManual = 0;
      enEjecucion = 0;
      enEspera = 0;
      contadorRebotes = 0;
      pasosElegidosNivel1 = 0;
      pasosMovimientoIntermedioElegidos = 0;
      pasosElegidosNivel2 = 0;
      cantidadPrimerNivel = 0;
      cantidadSegundoNivel = 0;
      digitalWrite(dir1, 0);
      digitalWrite(pulsos1, 0);
      digitalWrite(dir2, 0);
      digitalWrite(pulsos2, 0);
      encontrarHome();
    }
  }

  movimientoMotores();
  funcionManual();
  serialNextion();
  funcionAutomatico();
}
