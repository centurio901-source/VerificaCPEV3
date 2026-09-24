# ==============================================================================
# VALIDADOR DE COMPROBANTES - SUNAT
# Consulta integrada de validez de comprobantes mediante API SUNAT
# Streamlit
# ==============================================================================

import io
import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# ============================================================
# 🔐 BLOQUE DE INICIO DE SESIÓN
# ============================================================

USUARIO_CORRECTO = "admin"
CONTRASENA_CORRECTA = "123456"

# ---------- INICIALIZAR SESIÓN ----------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False


# ---------- PANTALLA DE LOGIN ----------
if not st.session_state.autenticado:

    st.set_page_config(
        page_title="Validación CPE COMPRAS",
        page_icon="🧾",
        layout="centered"
    )

    st.title("🧾 VALIDACIÓN CPE - SIRE - COMPRAS - SUNAT")
    st.subheader("🔐 Inicio de sesión")

    usuario = st.text_input(
        "Usuario",
        placeholder="Ingrese su usuario"
    )

    contrasena = st.text_input(
        "Contraseña",
        type="password",
        placeholder="Ingrese su contraseña"
    )

    if st.button("🔐 Ingresar", use_container_width=True):

        if (
            usuario == USUARIO_CORRECTO
            and contrasena == CONTRASENA_CORRECTA
        ):
            st.session_state.autenticado = True
            st.rerun()

        else:
            st.error("❌ Usuario o contraseña incorrectos.")

    st.stop()


# ============================================================
# BARRA LATERAL (LOGO Y DATOS DE CONTACTO)
# ============================================================   
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.info("💡 Sube 'logo.png' a GitHub para ver tu logo aquí.")

    st.markdown("---")
    st.markdown("""
    <div style="font-size:14px; line-height:1.6;">
        <div style="font-size:14px; color:#1F4E79; margin-bottom:5px;">
            <b>👨‍💻 Desarrollado por:</b>
        </div>
        <b>Karina T.Q.</b><br>
        <b>Magaly P.B.</b><br>
        <b>Versión V03</b><br>
        📱 <b>WhatsApp:</b> +51 928 859 231<br>
        💻 <b>AppWeb:</b> Validacion CPE Compras<br>
        📧 <b>Correo:</b> ---- ---- ----
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


# ==============================================================================
# CONFIGURACIÓN STREAMLIT
# ==============================================================================

st.set_page_config(
    page_title="VALIDACIÓN CPE - SIRE - COMPRAS - SUNAT",
    page_icon="🛡️",
    layout="wide"
)

# ==============================================================================
# ÍNDICES DEL TXT / EXCEL SIRE COMPRAS
# ==============================================================================

IDX_FECHA_EMISION = 5 - 1
IDX_TIPO_COMPROBANTE = 7 - 1
IDX_SERIE = 8 - 1
IDX_NUMERO = 10 - 1
IDX_TIPO_DOC_PROV = 12 - 1
IDX_RUC_PROV = 13 - 1
IDX_MONTO_TOTAL = 25 - 1


NOMBRES_COLUMNAS_SIRE = [
    "RUC Empresa",
    "Razon Social Empresa",
    "Periodo",
    "CAR SUNAT",
    "Fecha Emision",
    "Fecha Vcto/Pago",
    "Tipo CP",
    "Serie CP",
    "Anio",
    "Nro CP Inicial",
    "Nro CP Final",
    "Tipo Doc Prov",
    "RUC Proveedor",
    "Razon Social Proveedor",
    "BI Gravado DG",
    "IGV/IPM DG",
    "BI Gravado DGNG",
    "IGV/IPM DGNG",
    "BI Gravado DNG",
    "IGV/IPM DNG",
    "Valor Adq NG",
    "ISC",
    "ICBPER",
    "Otros Trib",
    "Total CP",
    "Moneda",
    "Tipo Cambio"
]


# ==============================================================================
# CÓDIGOS SUNAT
# ==============================================================================

MAP_ESTADO_CP = {
    "0": "0 - No existe",
    "1": "1 - Aceptado",
    "2": "2 - Anulado",
    "3": "3 - Autorizado",
    "4": "4 - No autorizado"
}


MAP_ESTADO_RUC = {
    "00": "00 - Activo",
    "01": "01 - Baja provisional",
    "02": "02 - Baja provisional de oficio",
    "03": "03 - Suspensión temporal",
    "10": "10 - Baja definitiva",
    "11": "11 - Baja de oficio",
    "22": "22 - Inhabilitado"
}


MAP_COND_DOMI_RUC = {
    "00": "00 - Habido",
    "09": "09 - Pendiente",
    "11": "11 - Por verificar",
    "12": "12 - No habido",
    "20": "20 - No hallado"
}


# ==============================================================================
# CLASE PRINCIPAL
# ==============================================================================

class ValidadorSUNAT:

    def __init__(self, ruc_empresa, client_id, client_secret):

        self.ruc_empresa = ruc_empresa.strip()
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()

        # --------------------------------------------------------------
        # Endpoint oficial para consulta integrada de comprobantes
        # --------------------------------------------------------------

        self.token_url = (
            "https://api-seguridad.sunat.gob.pe/"
            f"v1/clientesextranet/{self.client_id}/oauth2/token/"
        )

        self.valida_url = (
            "https://api.sunat.gob.pe/v1/contribuyente/"
            f"contribuyentes/{self.ruc_empresa}/validarcomprobante"
        )

        self.access_token = None


    # ==========================================================================
    # OBTENER TOKEN
    # ==========================================================================

    def obtener_token(self):

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        # --------------------------------------------------------------
        # IMPORTANTE:
        # SUNAT documenta client_credentials para este servicio.
        # Las credenciales van en el BODY.
        # --------------------------------------------------------------

        payload = {
            "grant_type": "client_credentials",
            "scope": (
                "https://api.sunat.gob.pe/"
                "v1/contribuyente/contribuyentes"
            ),
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:

            respuesta = requests.post(
                self.token_url,
                headers=headers,
                data=payload,
                timeout=30
            )

            # ----------------------------------------------------------
            # TOKEN CORRECTO
            # ----------------------------------------------------------

            if respuesta.status_code == 200:

                try:
                    datos = respuesta.json()
                except Exception:
                    st.error(
                        "SUNAT respondió correctamente, "
                        "pero la respuesta no tiene formato JSON."
                    )
                    return False

                token = datos.get("access_token")

                if token:

                    self.access_token = token

                    return True

                st.error(
                    "SUNAT no devolvió access_token.\n\n"
                    f"Respuesta: {datos}"
                )

                return False

            # ----------------------------------------------------------
            # ERROR DE AUTENTICACIÓN
            # ----------------------------------------------------------

            try:
                detalle = respuesta.json()
            except Exception:
                detalle = respuesta.text

            st.error(
                f"❌ Error de autenticación SUNAT\n\n"
                f"HTTP: {respuesta.status_code}\n\n"
                f"Respuesta:\n{detalle}"
            )

            return False

        except requests.exceptions.Timeout:

            st.error(
                "⏱️ SUNAT no respondió dentro del tiempo esperado."
            )

            return False

        except requests.exceptions.ConnectionError as e:

            st.error(
                "🌐 No se pudo establecer conexión con SUNAT.\n\n"
                f"{str(e)}"
            )

            return False

        except Exception as e:

            st.error(
                "❌ Error inesperado durante la autenticación.\n\n"
                f"{str(e)}"
            )

            return False


    # ==========================================================================
    # CONVERTIR FECHA A FORMATO SUNAT
    # ==========================================================================

    def convertir_fecha(self, fecha):

        fecha = str(fecha).strip()

        if not fecha:
            return None

        formatos = [
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d"
        ]

        for formato in formatos:

            try:

                fecha_obj = datetime.strptime(
                    fecha,
                    formato
                )

                return fecha_obj.strftime("%d/%m/%Y")

            except ValueError:
                pass

        return None


    # ==========================================================================
    # CONSULTAR COMPROBANTE
    # ==========================================================================

    def consultar_comprobante(
        self,
        ruc_emisor,
        tipo_cp,
        serie,
        numero,
        fecha,
        monto
    ):

        # --------------------------------------------------------------
        # Obtener token si todavía no existe
        # --------------------------------------------------------------

        if not self.access_token:

            if not self.obtener_token():

                return {
                    "error": "No se pudo obtener el token SUNAT."
                }


        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


        fecha_sunat = self.convertir_fecha(fecha)

        if not fecha_sunat:

            return {
                "error": (
                    f"Fecha inválida: {fecha}. "
                    "SUNAT requiere dd/mm/yyyy."
                )
            }


        # --------------------------------------------------------------
        # Datos que exige SUNAT
        # --------------------------------------------------------------

        payload = {
            "numRuc": str(ruc_emisor).strip(),
            "codComp": str(tipo_cp).strip().zfill(2),
            "numeroSerie": str(serie).strip(),
            "numero": int(numero),
            "fechaEmision": fecha_sunat,
            "monto": round(float(monto), 2)
        }


        try:

            respuesta = requests.post(
                self.valida_url,
                headers=headers,
                json=payload,
                timeout=30
            )


            # ----------------------------------------------------------
            # TOKEN VENCIDO
            # ----------------------------------------------------------

            if respuesta.status_code == 401:

                if self.obtener_token():

                    headers["Authorization"] = (
                        f"Bearer {self.access_token}"
                    )

                    respuesta = requests.post(
                        self.valida_url,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )

                else:

                    return {
                        "error": "SUNAT rechazó el token y no fue posible renovarlo."
                    }


            # ----------------------------------------------------------
            # RESPUESTA SUNAT
            # ----------------------------------------------------------

            try:
                datos = respuesta.json()
            except Exception:
                datos = {
                    "error": respuesta.text
                }


            if respuesta.status_code == 200:

                return datos


            return {
                "error": (
                    f"SUNAT HTTP {respuesta.status_code}: "
                    f"{datos}"
                )
            }


        except requests.exceptions.Timeout:

            return {
                "error": "SUNAT agotó el tiempo de espera."
            }


        except requests.exceptions.ConnectionError as e:

            return {
                "error": f"Error de conexión con SUNAT: {str(e)}"
            }


        except Exception as e:

            return {
                "error": f"Error consultando comprobante: {str(e)}"
            }


    # ==========================================================================
    # PROCESAR TXT / EXCEL SIRE
    # ==========================================================================

    def procesar_txt(self, archivo):

        resultado = {
            "total": 0,
            "correctos": 0,
            "errores": 0,
            "detalle": []
        }


        # --------------------------------------------------------------
        # LEER ARCHIVO TXT O EXCEL
        # --------------------------------------------------------------

        nombre_archivo = archivo.name.lower()

        # ==============================================================
        # EXCEL
        # ==============================================================

        if nombre_archivo.endswith(".xlsx"):

            try:

                df_excel = pd.read_excel(
                    archivo,
                    header=0,
                    dtype=object
                )

            except Exception as e:

                return {
                    "error": (
                        "No se pudo leer el archivo Excel.\n\n"
                        f"Detalle: {str(e)}"
                    )
                }


            # ----------------------------------------------------------
            # VALIDAR CANTIDAD DE COLUMNAS
            # ----------------------------------------------------------

            if len(df_excel.columns) < len(
                NOMBRES_COLUMNAS_SIRE
            ):

                return {
                    "error": (
                        "El archivo Excel no contiene "
                        "las 27 columnas esperadas del SIRE Compras."
                    )
                }


            # ----------------------------------------------------------
            # CONVERTIR EXCEL A LA MISMA ESTRUCTURA DEL TXT
            # ----------------------------------------------------------

            lineas = []


            for _, fila_excel in df_excel.iterrows():

                campos = []


                for i in range(
                    len(NOMBRES_COLUMNAS_SIRE)
                ):

                    valor = fila_excel.iloc[i]


                    # --------------------------------------------------
                    # CELDAS VACÍAS
                    # --------------------------------------------------

                    if pd.isna(valor):

                        valor = ""


                    else:

                        # ==============================================
                        # FECHA
                        # ==============================================

                        if i == IDX_FECHA_EMISION:

                            try:

                                if isinstance(
                                    valor,
                                    (datetime, pd.Timestamp)
                                ):

                                    valor = valor.strftime(
                                        "%d/%m/%Y"
                                    )

                                else:

                                    fecha_excel = pd.to_datetime(
                                        str(valor),
                                        errors="coerce",
                                        dayfirst=True
                                    )

                                    if not pd.isna(fecha_excel):

                                        valor = fecha_excel.strftime(
                                            "%d/%m/%Y"
                                        )

                            except Exception:

                                valor = str(valor).strip()


                        # ==============================================
                        # NÚMERO DE COMPROBANTE
                        # ==============================================

                        elif i == IDX_NUMERO:

                            try:

                                texto_numero = str(
                                    valor
                                ).strip()

                                numero_float = float(
                                    texto_numero
                                )

                                if numero_float.is_integer():

                                    valor = str(
                                        int(numero_float)
                                    )

                                else:

                                    valor = texto_numero

                            except Exception:

                                valor = str(valor).strip()


                        # ==============================================
                        # RUC DEL PROVEEDOR
                        # ==============================================

                        elif i == IDX_RUC_PROV:

                            try:

                                texto_ruc = str(
                                    valor
                                ).strip()

                                # Evitar valores como:
                                # 20123456789.0

                                if texto_ruc.endswith(".0"):

                                    texto_ruc = texto_ruc[:-2]


                                # Manejar eventualmente
                                # notación científica

                                if (
                                    "E" in texto_ruc.upper()
                                    or "." in texto_ruc
                                ):

                                    numero_ruc = float(
                                        texto_ruc
                                    )

                                    if numero_ruc.is_integer():

                                        texto_ruc = str(
                                            int(numero_ruc)
                                        )


                                valor = texto_ruc

                            except Exception:

                                valor = str(valor).strip()


                        # ==============================================
                        # MONTO TOTAL
                        # ==============================================

                        elif i == IDX_MONTO_TOTAL:

                            try:

                                if isinstance(
                                    valor,
                                    (int, float)
                                ):

                                    valor = f"{float(valor):.2f}"

                                else:

                                    texto_monto = str(
                                        valor
                                    ).strip()

                                    # Formato 1.500,50
                                    if (
                                        "," in texto_monto
                                        and "." in texto_monto
                                        and texto_monto.rfind(",")
                                        > texto_monto.rfind(".")
                                    ):

                                        texto_monto = (
                                            texto_monto
                                            .replace(".", "")
                                            .replace(",", ".")
                                        )

                                    # Formato 1500,50
                                    elif "," in texto_monto:

                                        texto_monto = (
                                            texto_monto
                                            .replace(",", ".")
                                        )

                                    valor = f"{float(texto_monto):.2f}"

                            except Exception:

                                valor = str(valor).strip()


                        # ==============================================
                        # RESTO DE CAMPOS
                        # ==============================================

                        else:

                            valor = str(
                                valor
                            ).strip()


                    campos.append(
                        str(valor)
                    )


                # ------------------------------------------------------
                # Convertir fila Excel a la misma estructura del TXT
                # ------------------------------------------------------

                lineas.append(
                    "|".join(campos)
                )


        # ==============================================================
        # TXT
        # ==============================================================

        elif nombre_archivo.endswith(".txt"):

            contenido = archivo.getvalue()

            lineas = None

            for encoding in [
                "utf-8-sig",
                "utf-8",
                "cp1252",
                "latin-1"
            ]:

                try:

                    lineas = contenido.decode(
                        encoding
                    ).splitlines()

                    break

                except UnicodeDecodeError:

                    continue


            if lineas is None:

                return {
                    "error": "No se pudo leer el archivo TXT."
                }


        # ==============================================================
        # FORMATO NO PERMITIDO
        # ==============================================================

        else:

            return {
                "error": (
                    "Formato de archivo no permitido. "
                    "Utilice TXT o Excel (.xlsx)."
                )
            }


        # --------------------------------------------------------------
        # ÍNDICE MÁXIMO NECESARIO
        # --------------------------------------------------------------

        max_idx = max(
            IDX_FECHA_EMISION,
            IDX_TIPO_COMPROBANTE,
            IDX_SERIE,
            IDX_NUMERO,
            IDX_TIPO_DOC_PROV,
            IDX_RUC_PROV,
            IDX_MONTO_TOTAL
        )


        # --------------------------------------------------------------
        # OBTENER TOKEN UNA SOLA VEZ
        # --------------------------------------------------------------

        with st.spinner(
            "🔐 Autenticando con SUNAT..."
        ):

            if not self.obtener_token():

                return {
                    "error": (
                        "No fue posible autenticarse "
                        "con SUNAT."
                    )
                }


        # --------------------------------------------------------------
        # PROCESAR CADA LÍNEA
        # --------------------------------------------------------------

        for numero_linea, linea in enumerate(
            lineas,
            start=1
        ):

            linea = linea.rstrip("\r\n")

            if not linea.strip():
                continue


            campos = linea.split("|")


            # ----------------------------------------------------------
            # VALIDAR ESTRUCTURA
            # ----------------------------------------------------------

            if len(campos) <= max_idx:

                continue


            ruc_proveedor = campos[
                IDX_RUC_PROV
            ].strip()


            if (
                not ruc_proveedor.isdigit()
                or len(ruc_proveedor) != 11
            ):

                continue


            resultado["total"] += 1


            errores = []


            estado_cp = "No consultado"
            estado_ruc = "No consultado"
            cond_domi = "No consultado"


            # ----------------------------------------------------------
            # EXTRAER DATOS
            # ----------------------------------------------------------

            fecha = campos[
                IDX_FECHA_EMISION
            ].strip()


            tipo_cp = campos[
                IDX_TIPO_COMPROBANTE
            ].strip().zfill(2)


            serie = campos[
                IDX_SERIE
            ].strip()


            numero = campos[
                IDX_NUMERO
            ].strip()


            # ----------------------------------------------------------
            # MONTO
            # ----------------------------------------------------------

            monto_raw = campos[
                IDX_MONTO_TOTAL
            ].strip()


            try:

                monto = round(
                    float(monto_raw),
                    2
                )

            except ValueError:

                monto = 0.0

                errores.append(
                    "Monto total no numérico."
                )


            # ----------------------------------------------------------
            # VALIDACIONES LOCALES
            # ----------------------------------------------------------

            tipos_permitidos = {
                "01",
                "03",
                "04",
                "07",
                "08",
                "12",
                "14",
                "91"
            }


            if tipo_cp not in tipos_permitidos:

                errores.append(
                    f"Tipo de comprobante inválido: {tipo_cp}"
                )


            if not numero.isdigit():

                errores.append(
                    f"Número de comprobante inválido: {numero}"
                )


            # ----------------------------------------------------------
            # CONSULTAR SUNAT
            # ----------------------------------------------------------

            if not errores:

                respuesta = self.consultar_comprobante(
                    ruc_emisor=ruc_proveedor,
                    tipo_cp=tipo_cp,
                    serie=serie,
                    numero=numero,
                    fecha=fecha,
                    monto=monto
                )


                if "error" in respuesta:

                    errores.append(
                        respuesta["error"]
                    )

                else:

                    data = respuesta.get(
                        "data",
                        {}
                    )


                    val_estado_cp = str(
                        data.get(
                            "estadoCp",
                            ""
                        )
                    ).strip()


                    val_estado_ruc = str(
                        data.get(
                            "estadoRuc",
                            ""
                        )
                    ).strip()


                    val_cond_domi = str(
                        data.get(
                            "condDomiRuc",
                            ""
                        )
                    ).strip()


                    estado_cp = MAP_ESTADO_CP.get(
                        val_estado_cp,
                        f"{val_estado_cp} - Desconocido"
                    )


                    estado_ruc = MAP_ESTADO_RUC.get(
                        val_estado_ruc,
                        f"{val_estado_ruc} - Desconocido"
                    )


                    cond_domi = MAP_COND_DOMI_RUC.get(
                        val_cond_domi,
                        f"{val_cond_domi} - Desconocido"
                    )


                    # --------------------------------------------------
                    # ESTADO DEL COMPROBANTE
                    # --------------------------------------------------

                    if val_estado_cp != "1":

                        errores.append(
                            f"SUNAT: {estado_cp}"
                        )


                    # --------------------------------------------------
                    # ESTADO DEL RUC
                    # --------------------------------------------------

                    if val_estado_ruc != "00":

                        errores.append(
                            f"SUNAT RUC: {estado_ruc}"
                        )


                    # --------------------------------------------------
                    # DOMICILIO
                    # --------------------------------------------------

                    if val_cond_domi != "00":

                        errores.append(
                            f"SUNAT domicilio: {cond_domi}"
                        )


                    # --------------------------------------------------
                    # OBSERVACIONES SUNAT
                    # --------------------------------------------------

                    observaciones = data.get(
                        "observaciones",
                        []
                    )


                    if isinstance(
                        observaciones,
                        list
                    ):

                        for obs in observaciones:

                            if obs:

                                errores.append(
                                    str(obs)
                                )


            # ----------------------------------------------------------
            # CONSTRUIR RESULTADO
            # ----------------------------------------------------------

            fila = {}


            for i, nombre in enumerate(
                NOMBRES_COLUMNAS_SIRE
            ):

                fila[nombre] = (
                    campos[i].strip()
                    if i < len(campos)
                    else ""
                )


            fila["Estado Validación"] = (
                "ERROR"
                if errores
                else "OK"
            )


            fila["Estado Comprobante SUNAT"] = (
                estado_cp
            )


            fila["Estado RUC SUNAT"] = (
                estado_ruc
            )


            fila["Condición Domicilio SUNAT"] = (
                cond_domi
            )


            fila["Detalle Alerta"] = (
                " | ".join(errores)
                if errores
                else "Comprobante válido según consulta SUNAT."
            )


            fila["Línea TXT"] = numero_linea


            if errores:

                resultado["errores"] += 1

            else:

                resultado["correctos"] += 1


            resultado["detalle"].append(
                fila
            )


        return resultado


# ==============================================================================
# INTERFAZ
# ==============================================================================

st.title(
    "🛡️ VALIDACIÓN CPE - SIRE - COMPRAS - SUNAT"
)

st.markdown(
    """
    **Consulta integrada de validez de comprobantes de pago
    mediante el servicio web de SUNAT.**
    """
)


# ==============================================================================
# BARRA LATERAL
# ==============================================================================

with st.sidebar:

    st.header("🔐 Credenciales SUNAT")

    st.info(
        """
        Utilice las credenciales API generadas
        desde SUNAT Operaciones en Línea.
        """
    )


    ruc_input = st.text_input(
        "RUC de la empresa que realiza la consulta",
        max_chars=11,
        placeholder="20123456789"
    )


    client_id_input = st.text_input(
        "Client ID",
        type="password"
    )


    client_secret_input = st.text_input(
        "Client Secret",
        type="password"
    )


    st.divider()


    st.caption(
        "Las credenciales no se muestran en el reporte."
    )


# ==============================================================================
# ARCHIVO
# ==============================================================================

archivo = st.file_uploader(
    "📂 Cargue el TXT oficial del SIRE Compras o archivo Excel",
    type=["txt", "xlsx"]
)


# ==============================================================================
# PROCESAR
# ==============================================================================

if archivo is not None:

    st.success(
        f"Archivo seleccionado: {archivo.name}"
    )


    if st.button(
        "🚀 INICIAR VALIDACIÓN SUNAT",
        type="primary",
        use_container_width=True
    ):


        # --------------------------------------------------------------
        # VALIDAR CREDENCIALES
        # --------------------------------------------------------------

        if not ruc_input:

            st.error(
                "Ingrese el RUC de la empresa."
            )

            st.stop()


        if not ruc_input.isdigit() or len(ruc_input) != 11:

            st.error(
                "El RUC debe contener exactamente 11 dígitos."
            )

            st.stop()


        if not client_id_input:

            st.error(
                "Ingrese el Client ID."
            )

            st.stop()


        if not client_secret_input:

            st.error(
                "Ingrese el Client Secret."
            )

            st.stop()


        # --------------------------------------------------------------
        # CREAR VALIDADOR
        # --------------------------------------------------------------

        validador = ValidadorSUNAT(
            ruc_empresa=ruc_input,
            client_id=client_id_input,
            client_secret=client_secret_input
        )


        # --------------------------------------------------------------
        # PROCESAR
        # --------------------------------------------------------------

        with st.spinner(
            "🔄 Consultando comprobantes directamente con SUNAT..."
        ):

            resultado = validador.procesar_txt(
                archivo
            )


        # --------------------------------------------------------------
        # ERROR GENERAL
        # --------------------------------------------------------------

        if "error" in resultado:

            st.error(
                resultado["error"]
            )

            st.stop()


        # --------------------------------------------------------------
        # RESUMEN
        # --------------------------------------------------------------

        st.success(
            "✅ Proceso de validación finalizado."
        )


        col1, col2, col3 = st.columns(3)


        col1.metric(
            "Comprobantes procesados",
            resultado["total"]
        )


        col2.metric(
            "Comprobantes OK",
            resultado["correctos"]
        )


        col3.metric(
            "Comprobantes con alertas",
            resultado["errores"]
        )


        st.divider()


        # --------------------------------------------------------------
        # DATAFRAME
        # --------------------------------------------------------------

        df = pd.DataFrame(
            resultado["detalle"]
        )


        st.subheader(
            "📋 Resultado de validación"
        )


        st.dataframe(
            df,
            use_container_width=True,
            height=600
        )


        # --------------------------------------------------------------
        # DESCARGA XLSX
        # --------------------------------------------------------------

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Validación SUNAT"
            )

        nombre_salida = (
            "Resultado_Validacion_SUNAT_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        st.download_button(
            label="📥 Descargar resultado en Excel",
            data=buffer.getvalue(),
            file_name=nombre_salida,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )