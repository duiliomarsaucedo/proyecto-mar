import os

class Proceso:
    def __init__(self, pid, prioridad, tiempo_ejecucion):
        self.pid = pid
        self.estado = "listo"
        self.prioridad = prioridad
        self.tiempo_ejecucion = tiempo_ejecucion
        self.recursos = {"cpu": 0, "memoria": 0}
        self.mensajes = []
        self.causa_terminacion = None

    def __str__(self):
        return f"Proceso {self.pid} | Estado: {self.estado} | Prioridad: {self.prioridad} | Tiempo: {self.tiempo_ejecucion} | Recursos: {self.recursos}"

    def enviar_mensaje(self, mensaje, destino):
        destino.mensajes.append(mensaje)
        print(f"Proceso {self.pid} envió mensaje '{mensaje}' a Proceso {destino.pid}")

    def recibir_mensaje(self):
        if self.mensajes:
            mensaje = self.mensajes.pop(0)
            print(f"Proceso {self.pid} recibió mensaje: '{mensaje}'")
            return mensaje
        return None

    def terminar(self, causa):
        self.estado = "terminado"
        self.causa_terminacion = causa
        print(f"Proceso {self.pid} terminó por: {causa}")

class GestorRecursos:
    def __init__(self):
        self.cpu_disponible = 1
        self.memoria_disponible = 4096

    def solicitar_recursos(self, proceso, cpu, memoria):
        if self.cpu_disponible >= cpu and self.memoria_disponible >= memoria:
            self.cpu_disponible -= cpu
            self.memoria_disponible -= memoria
            proceso.recursos["cpu"] += cpu
            proceso.recursos["memoria"] += memoria
            print(f"Proceso {proceso.pid} recibió CPU: {cpu}, Memoria: {memoria}")
            return True
        else:
            print(f"Proceso {proceso.pid}: No hay suficientes recursos")
            return False

    def liberar_recursos(self, proceso):
        self.cpu_disponible += proceso.recursos["cpu"]
        self.memoria_disponible += proceso.recursos["memoria"]
        print(f"Proceso {proceso.pid} liberó CPU: {proceso.recursos['cpu']}, Memoria: {proceso.recursos['memoria']}")
        proceso.recursos["cpu"] = 0
        proceso.recursos["memoria"] = 0

class Semaforo:
    def __init__(self, valor_inicial):
        self.valor = valor_inicial

    def wait(self, proceso):
        self.valor -= 1
        if self.valor < 0:
            proceso.estado = "esperando"
            print(f"Proceso {proceso.pid} está esperando en el semáforo")
            return False
        return True

    def signal(self, proceso):
        self.valor += 1
        print(f"Proceso {proceso.pid} liberó el semáforo")
        if self.valor <= 0:
            return True
        return False

class ProductorConsumidor:
    def __init__(self, capacidad_buffer):
        self.buffer = []
        self.capacidad_buffer = capacidad_buffer
        self.semaforo_productor = Semaforo(capacidad_buffer)
        self.semaforo_consumidor = Semaforo(0)

    def producir(self, proceso, mensaje):
        if self.semaforo_productor.wait(proceso):
            self.buffer.append(mensaje)
            print(f"Proceso {proceso.pid} produjo: {mensaje}")
            self.semaforo_consumidor.signal(proceso)
            return True
        return False

    def consumir(self, proceso):
        if self.semaforo_consumidor.wait(proceso):
            mensaje = self.buffer.pop(0)
            print(f"Proceso {proceso.pid} consumió: {mensaje}")
            self.semaforo_productor.signal(proceso)
            return mensaje
        return False

class Planificador:
    def __init__(self, algoritmo, quantum=2):
        self.cola_listos = []
        self.proceso_actual = None
        self.algoritmo = algoritmo
        self.quantum = quantum
        self.tiempo_total = 0

    def agregar_proceso(self, proceso):
        self.cola_listos.append(proceso)
        proceso.estado = "listo"
        print(f"Proceso {proceso.pid} añadido a la cola de listos")

    def ejecutar(self, gestor_recursos):
        if not self.cola_listos and not self.proceso_actual:
            print("No hay procesos para ejecutar")
            return False

        if not self.proceso_actual:
            self.seleccionar_proceso()

        if self.proceso_actual:
            if gestor_recursos.solicitar_recursos(self.proceso_actual, 1, 1000):
                self.proceso_actual.estado = "ejecutando"
                print(f"Ejecutando {self.proceso_actual}")

                # Ejecutar solo 1 unidad de tiempo por ciclo (excepto en RR)
                tiempo_corrido = min(self.quantum if self.algoritmo == "RR" else 1, self.proceso_actual.tiempo_ejecucion)

                self.proceso_actual.tiempo_ejecucion -= tiempo_corrido
                self.tiempo_total += tiempo_corrido

                if self.proceso_actual.tiempo_ejecucion <= 0:
                    self.proceso_actual.terminar("Finalización normal")
                    gestor_recursos.liberar_recursos(self.proceso_actual)
                    self.proceso_actual = None
                else:
                    if self.algoritmo == "RR":
                        self.proceso_actual.estado = "listo"
                        self.cola_listos.append(self.proceso_actual)
                        self.proceso_actual = None

        return True

    def seleccionar_proceso(self):
        if not self.cola_listos:
            return

        if self.algoritmo == "FCFS":
            self.proceso_actual = self.cola_listos.pop(0)
        elif self.algoritmo == "SJF":
            self.proceso_actual = min(self.cola_listos, key=lambda p: p.tiempo_ejecucion)
            self.cola_listos.remove(self.proceso_actual)
        elif self.algoritmo == "Prioridad":
            self.proceso_actual = min(self.cola_listos, key=lambda p: p.prioridad)
            self.cola_listos.remove(self.proceso_actual)
        elif self.algoritmo == "RR":
            self.proceso_actual = self.cola_listos.pop(0)

    def terminar_proceso(self, pid, gestor_recursos):
        for proceso in self.cola_listos:
            if proceso.pid == pid:
                proceso.terminar("Terminación forzada")
                self.cola_listos.remove(proceso)
                gestor_recursos.liberar_recursos(proceso)
                return True
        if self.proceso_actual and self.proceso_actual.pid == pid:
            self.proceso_actual.terminar("Terminación forzada")
            gestor_recursos.liberar_recursos(self.proceso_actual)
            self.proceso_actual = None
            return True
        print(f"Proceso {pid} no encontrado")
        return False

class Simulador:
    def __init__(self):
        self.gestor = GestorRecursos()
        self.planificador = None
        self.logs = []

    def log_evento(self, mensaje):
        self.logs.append(mensaje)
        print(mensaje)

    def mostrar_menu(self):
        os.system('clear')
        print("=== Simulador de Gestor de Procesos ===")
        print("1. Seleccionar algoritmo de planificación")
        print("2. Crear proceso")
        print("3. Listar procesos")
        print("4. Listar recursos disponibles")
        print("5. Ejecutar un ciclo")
        print("6. Terminar proceso")
        print("7. Suspender proceso")
        print("8. Reanudar proceso")
        print("9. Mostrar logs")
        print("10. Salir")
        return input("Elige una opción: ")

    def seleccionar_algoritmo(self):
        print("Algoritmos disponibles: FCFS, SJF, Prioridad, RR")
        algoritmo = input("Ingresa el algoritmo: ").upper()
        if algoritmo in ["FCFS", "SJF", "Prioridad", "RR"]:
            quantum = 2
            if algoritmo == "RR":
                try:
                    quantum = int(input("Ingresa el quantum: "))
                    if quantum <= 0:
                        print("Error: El quantum debe ser positivo. Usando quantum = 2.")
                        quantum = 2
                except ValueError:
                    print("Error: Ingresa un número válido. Usando quantum = 2.")
                    quantum = 2
            self.planificador = Planificador(algoritmo, quantum)
            self.log_evento(f"Algoritmo seleccionado: {algoritmo}")
        else:
            print("Algoritmo no válido")

    def crear_proceso(self):
        if not self.planificador:
            print("Selecciona un algoritmo primero")
            return
        while True:
            try:
                pid = int(input("Ingresa el PID del proceso: "))
                # Verificar si el PID ya está en uso
                if any(proceso.pid == pid for proceso in self.planificador.cola_listos) or \
                   (self.planificador.proceso_actual and self.planificador.proceso_actual.pid == pid):
                    print("Error: El PID ya está en uso. Ingresa un PID diferente.")
                    continue
                if pid <= 0:
                    print("Error: El PID debe ser un número positivo.")
                    continue
                break
            except ValueError:
                print("Error: Ingresa un número válido para el PID.")
        
        while True:
            try:
                prioridad = int(input("Ingresa la prioridad (1-10): "))
                if 1 <= prioridad <= 10:
                    break
                print("Error: La prioridad debe estar entre 1 y 10.")
            except ValueError:
                print("Error: Ingresa un número válido para la prioridad.")
        
        while True:
            try:
                tiempo = int(input("Ingresa el tiempo de ejecución: "))
                if tiempo > 0:
                    break
                print("Error: El tiempo de ejecución debe ser positivo.")
            except ValueError:
                print("Error: Ingresa un número válido para el tiempo.")
        
        proceso = Proceso(pid, prioridad, tiempo)
        self.planificador.agregar_proceso(proceso)
        self.log_evento(f"Proceso {pid} creado")

    def listar_procesos(self):
        if not self.planificador:
            print("Selecciona un algoritmo primero")
            return
        print("Procesos en la cola de listos:")
        if not self.planificador.cola_listos:
            print("[Vacío]")
        for proceso in self.planificador.cola_listos:
            print(proceso)
        print("Proceso actual:")
        if self.planificador.proceso_actual:
            print(self.planificador.proceso_actual)
        else:
            print("[Vacío]")

    def listar_recursos(self):
        print(f"CPU disponible: {self.gestor.cpu_disponible}")
        print(f"Memoria disponible: {self.gestor.memoria_disponible} MB")

    def ejecutar_ciclo(self):
        if not self.planificador:
            print("Selecciona un algoritmo primero")
            return
        self.planificador.ejecutar(self.gestor)

    def terminar_proceso(self):
        if not self.planificador:
            print("Selecciona un algoritmo primero")
            return
        try:
            pid = int(input("Ingresa el PID del proceso: "))
            self.planificador.terminar_proceso(pid, self.gestor)
        except ValueError:
            print("Error: Ingresa un número válido para el PID.")

    def suspender_proceso(self):
        if not self.planificador:
            print("Selecciona un algoritmo primero")
            return
        try:
            pid = int(input("Ingresa el PID del proceso: "))
            if self.planificador.proceso_actual and self.planificador.proceso_actual.pid == pid:
                self.planificador.proceso_actual.estado = "esperando"
                self.planificador.cola_listos.append(self.planificador.proceso_actual)
                self.log_evento(f"Proceso {pid} suspendido")
                self.planificador.proceso_actual = None
            else:
                print("Proceso no encontrado o no está ejecutando")
        except ValueError:
            print("Error: Ingresa un número válido para el PID.")

    def reanudar_proceso(self):
        if not self.planificador:
            print("Selecciona un algoritmo primero")
            return
        try:
            pid = int(input("Ingresa el PID del proceso: "))
            for proceso in self.planificador.cola_listos:
                if proceso.pid == pid and proceso.estado == "esperando":
                    proceso.estado = "listo"
                    self.log_evento(f"Proceso {pid} reanudado")
                    return
            print("Proceso no encontrado o no está suspendido")
        except ValueError:
            print("Error: Ingresa un número válido para el PID.")

    def mostrar_logs(self):
        print("=== Logs de eventos ===")
        if not self.logs:
            print("[Vacío]")
        for log in self.logs:
            print(log)

    def correr(self):
        while True:
            opcion = self.mostrar_menu()
            try:
                opcion = int(opcion)
            except ValueError:
                print("Opción no válida")
                input("Presiona Enter para continuar...")
                continue
            if opcion == 1:
                self.seleccionar_algoritmo()
            elif opcion == 2:
                self.crear_proceso()
            elif opcion == 3:
                self.listar_procesos()
            elif opcion == 4:
                self.listar_recursos()
            elif opcion == 5:
                self.ejecutar_ciclo()
            elif opcion == 6:
                self.terminar_proceso()
            elif opcion == 7:
                self.suspender_proceso()
            elif opcion == 8:
                self.reanudar_proceso()
            elif opcion == 9:
                self.mostrar_logs()
            elif opcion == 10:
                print("Saliendo del simulador")
                break
            else:
                print("Opción no válida")
            input("Presiona Enter para continuar...")

# Iniciamos el simulador
simulador = Simulador()
simulador.correr()



            

