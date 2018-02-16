#!/usr/bin/env python
# coding:utf-8

from __future__ import print_function
from os import getenv, getcwd, path, remove, mkdir, system
from time import sleep
from subprocess import Popen
from sys import platform
import logging
from shutil import move
import signal
import argparse
from concurrent.futures import ThreadPoolExecutor, wait
from requests import get, packages
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from colored import fg, bg, attr


__autor__ = 'Henry Vasquez Conde'
__correo__ = 'lifehack.py@gmail.com'
__version__ = '1.3'


class FreneticDL(object):
    def __init__(self):
        self.UserAgent = ''
        self.contador = 0
        self.part = 0
        self.segmentos = 50
        self.hilos = 3
        self.reconect = 100
        self.BytesDescargados = 0
        self.file_size_Megas = 0
        self.porcentaje = 0
        self.megas_float = 0
        self.rate = 0
        self.restante = 0
        self.scan = True
        self.finish = False
        self.Intervalo = 0
        self.ListIntervalo = []
        self.abort = False
        self.pause = False
        self.StateFile = 'wait'
        self.abort_stream = False
        self.UrlFaill = False
        self.NetError = False
        self.Lista_Pool = []
        self.cookie = ''
        self.startPorcen = 5
        self.new_len = 0
        self.pwd = ''
        self.Intentos_Segmentos = {}
        self.tmp = r'/tmp/'
        self.NotRangeSupport = False
        self.setColor = lambda c, d: '%s%s %s %s' % (fg(0), bg(c), d, attr('reset'))
        self.verde = lambda d: self.setColor(85, d)
        self.rojo = lambda d: self.setColor(202, d)
        self.akua = lambda d: self.setColor(122, d)
        self.config()

    def config(self):
        signal.signal(signal.SIGINT, self.change_estate)
        packages.urllib3.disable_warnings(InsecureRequestWarning)
        logging.basicConfig(
                            level=logging.INFO,
                            format=' %(levelname)s : %(message)s'
                            )

    def change_estate(self, signum, frame):
        if not self.pause:
            self.pause = True
            self.StateFile = self.rojo('pause')
        else:
            self.pause = False
            self.StateFile = self.verde('run')

    def Concat(self, filename, ruta):
        try:
            if not path.exists(ruta):
                mkdir(ruta)
                logging.info(self.akua('carpeta creada'))

            self.pwd = path.join(ruta, filename)

            with open(self.pwd, "wb") as file:
                for i in range(self.segmentos):
                    with open(path.join(self.tmp, filename + str(i + 1)), "rb") as p:
                        parte = p.read()
                        file.seek(self.part * i)
                        file.tell()
                        file.write(parte)
                    sleep(0.01)

            if path.exists(self.pwd):
                for i in range(self.segmentos):
                    remove(path.join(self.tmp, filename + str(i + 1)))
        except Exception as e:
            logging.debug(unicode(e))

    # reproducir videos mientras se descarga. /7solo funciona en gnu/linux, problemas en windows
    def ConcatPlay(self, filename, ruta):
        try:
            with open(path.join(ruta, filename), "wb") as file:
                for i in range(self.segmentos):
                    while True:
                        while not path.exists(path.join(ruta, filename + str(i + 1))):
                            sleep(0.3)
                        try:
                            with open(path.join(ruta, filename+str(i + 1)), "rb") as p:
                                parte = p.read()
                                if self.part+1 == len(parte):
                                    file.seek(self.part * i)
                                    file.tell()
                                    file.write(parte)
                                    break
                                if self.abort_stream:
                                    return
                                sleep(0.3)
                        except Exception as e:
                            logging.debug(unicode(e))
        except Exception as e:
            logging.debug(unicode(e))
        finally:
            remove(path.join(ruta, filename))

    def PlayVideo(self, binary):
        if platform == 'linux2':
            # totem,vlc,dragon
            cmd = '{0} "{1}"'.format(binary, path.join(getcwd(), self.tmp, self.filename))
        elif platform == 'win32':
            # wmplayer = path.join(getenv('PROGRAMFILES') ,'Windows Media Player' ,'wmplayer.exe')
            vlc = path.join(getenv('PROGRAMFILES'), 'VideoLAN', 'VLC', 'vlc.exe')
            cmd = '"{0}" "{1}"'.format(vlc, path.join(getcwd(), self.tmp, self.filename))

        sleep(3)
        proc = Popen(cmd, shell=True)
        proc.wait()
        self.abort_stream = True

    def Handler(self, start, end, url, file_temp):
        self.Intentos_Segmentos[file_temp] += 1

        try:
            t = 0
            self.StateFile = self.verde('run')
            Newstart = start
            if self.abort:
                return
            if path.exists(path.join(self.tmp, file_temp)):
                with open(path.join(self.tmp, file_temp), "rb") as f:
                    t = len(f.read())

                    if t == self.part+1:    # Completo
                        logging.debug('utilizando segmento..')
                        self.BytesDescargados += t
                        self.contador += 1
                        return
                    else:   # parcial
                        logging.debug('continuando descarga...')
                        Newstart += t

            logging.debug('download part {0}'.format(file_temp))
            headers = {
                        'Range': 'bytes=%d-%d' % (Newstart, end),
                        'User-Agent': self.UserAgent,
                        'cookie': self.cookie
                        }

            req = get(url, headers=headers, stream=True, verify=False, timeout=10, allow_redirects=True)
            self.stream_download(req, file_temp, Newstart)

            with open(path.join(self.tmp, file_temp), "rb") as f:
                tm = len(f.read())

            if (tm == self.part + 1) or (tm == self.new_len):
                self.contador += 1
            else:
                if (tm > self.part + 1):
                    remove(path.join(self.tmp, file_temp))
                    logging.debug('ELIMINANDO SEGMENTO')
                elif (self.new_len > 0) and (tm > self.new_len):
                        remove(path.join(self.tmp, file_temp))
                        logging.debug('ELIMINANDO SEGMENTO')
                logging.debug('Error segmento no coincide %d/%d /%dreboot segmento!%s ' % (
                    tm, self.part,
                    self.new_len, file_temp)
                )
                raise Exception('segmento')

        except Exception as e:
            logging.debug(self.Intentos_Segmentos[file_temp])
            logging.debug(unicode(e))
            if u'content-range' in unicode(e):
                if self.Intentos_Segmentos[file_temp] == 5:
                    self.NotRangeSupport = True
                    return
            elif u'peso_no_coincide' in unicode(e):
                if self.Intentos_Segmentos[file_temp] == 5:
                    self.UrlFaill = True
                    return
            elif self.Intentos_Segmentos[file_temp] == self.reconect:
                self.UrlFaill = True
                return
            sleep(10)
            return self.Handler(start, end, url, file_temp)

    def download_file(self, url, filename, folder, cookie, UserAgent, reconect, threads, play):
        self.cookie = cookie
        self.UserAgent = UserAgent
        self.enlace = url
        self.reconect = reconect
        self.hilos = threads
        self.play = play

        if not filename:
            self.filename = url.split('/')[-1]

        logging.info(url)

        header = {
                    'User-Agent': self.UserAgent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': "en-US,en;q=0.5",
                    'Accept-Encoding': "gzip, deflate",
                    'Range': 'bytes=0-10000',
                    'cookie': self.cookie
                    }

        try:
            r = get(url, verify=False, headers=header, timeout=10, allow_redirects=True)
            self.pesoTotal = r.headers['content-range']
            self.pesoTotal = int(self.pesoTotal.split('/')[-1])
            self.file_size_Megas = format(self.pesoTotal / (1024. * 1024.), '.1f')
            self.segmentos = int(float(self.file_size_Megas) / 2)

        except Exception as e:
            print(e)
            if u'Connection aborted' in unicode(e):
                self.NetError = True
                return
            elif u'content-range' in unicode(e):
                logging.info(self.rojo('HEAD Range no soportado.'))
                self.NotRangeSupport = True
            else:
                self.UrlFaill = True
                return

        if self.NotRangeSupport or not self.segmentos:
            exe = ThreadPoolExecutor(1)
            exe.submit(self.EstadoDownload)
            self.direct_download(url, self.filename, header, folder)
            self.scan = False
            return

        self.part = self.pesoTotal / (int(self.segmentos))

        exe = ThreadPoolExecutor(1)
        exe.submit(self.EstadoDownload)

        self.Lista_Pool2 = []

        executor = ThreadPoolExecutor(max_workers=self.hilos)
        for i in range(self.segmentos):
            while executor._work_queue.qsize() >= self.hilos:
                sleep(0.3)

            if self.NotRangeSupport:
                self.scan = False
                break
            elif self.abort:
                self.scan = False
                for i in range(self.segmentos):
                    try:
                        remove(path.join(self.tmp, self.filename + str(i + 1)))
                    except:
                        pass
                break
            start = self.part * i
            end = start + self.part
            self.new_len = 0
            if i == (self.segmentos - 1):
                self.new_len = self.pesoTotal - start
                end = self.pesoTotal

            self.Intentos_Segmentos[self.filename + str(i + 1)] = 0
            pool = executor.submit(self.Handler, start, end, url, self.filename + str(i + 1))
            self.Lista_Pool.append(pool)

        wait(self.Lista_Pool)
        if self.contador == self.segmentos:
            self.finish = True
            self.StateFile = self.verde('completo')
            self.porcentaje = '100'

            unir = ThreadPoolExecutor(1)
            self.Lista_Pool2.append(unir.submit(self.Concat, self.filename, folder))
            wait(self.Lista_Pool2)
            self.scan = False
            sleep(1)
            logging.info(self.akua('%s Descargado con Exito!' % (self.filename)))
            logging.info(self.akua('salida:  %s' % (self.pwd)))

        else:
            self.UrlFaill = True
            self.scan = False

    def direct_download(self, url, filename, header, folder):
        del header['Range']
        req = get(url, verify=False, stream=True, headers=header, timeout=120, allow_redirects=True)
        self.pesoTotal = int(req.headers['Content-Length'])
        self.file_size_Megas = format(self.pesoTotal / (1024. * 1024.), '.1f')
        self.stream_download(req, filename)
        src = path.join(self.tmp, filename)
        dest = path.join(folder, filename)
        move(src, dest)

    def stream_download(self, req, file_temp, sek=None):
        with open(path.join(self.tmp, file_temp), "ab+") as f:
            if not (sek is None):
                f.seek(sek)
                f.tell()

            for chunk in req.iter_content(chunk_size=1024):
                if self.abort:
                    return
                while self.pause:
                    if self.abort:
                        return
                    sleep(1)
                if chunk:
                    self.BytesDescargados += len(chunk)
                    f.write(chunk)

    def time_read(self, duration, fmt_short=False):
        duration = int(duration)
        if duration == 0:
            return "0s" if fmt_short else "0 segundos"

        INTERVALS = [1, 60, 3600, 86400]
        if fmt_short:
            NAMES = ['s' * 2, 'm' * 2, 'h' * 2, 'd' * 2]
        else:
            NAMES = [
                ('segundo', 'segundos'),
                ('minuto', 'minutos'),
                ('hora', 'horas'),
                ('dia', 'dias')
                ]

        result = []

        for i in range(len(NAMES)-1, -1, -1):
            a = duration // INTERVALS[i]
            if a > 0:
                result.append((a, NAMES[i][1 % a]))
                duration -= a * INTERVALS[i]

        if fmt_short:
            return "".join(["%s%s " % x for x in result])
        return ", ".join(["%s %s" % x for x in result])

    def EstadoDownload(self):
        self.freezeRate = ''
        self.freezeRestante = ''

        while self.scan:
            try:
                if not self.finish:
                    megas = float(self.BytesDescargados) / (1024.0 * 1024.0)
                    self.megas_float = format(megas, '.2f')
                    self.porcentaje = (float(self.BytesDescargados) / float(self.pesoTotal)) * 100.0
                    self.barra = self.porcentaje
                    self.porcentaje = format(self.porcentaje, '.2f')

                    if self.play and self.barra >= self.startPorcen:
                        unir = ThreadPoolExecutor(1)
                        unir.submit(self.ConcatPlay, self.filename, self.tmp)
                        play = ThreadPoolExecutor(1)
                        play.submit(self.PlayVideo, self.play.lower())
                        self.play = False

                else:
                    self.porcentaje = '100'     # evitar 99.9 fix
                    self.barra = 100
                    self.megas_float = str(self.file_size_Megas)

                if len(self.ListIntervalo) == 10:
                    self.ListIntervalo.pop(0)

                newBytes = (float(self.BytesDescargados) - self.Intervalo) / 1024.0
                self.Intervalo = self.BytesDescargados
                self.ListIntervalo.append(newBytes)
                self.rate = sum(self.ListIntervalo)

                INF = '{0}/{1}M \t  Porcentaje: {2} %'.format(
                        self.megas_float,
                        self.file_size_Megas,
                        self.porcentaje
                        )
                self.barra = '[%s%s]' % ('#' * int(self.barra), ' ' * (100 - int(self.barra)))
                self.barra = self.verde(self.barra)

                if self.rate > 0:
                    self.restante = int((self.pesoTotal - self.BytesDescargados) / 1024 / self.rate)
                    if self.rate < 1024:
                        self.rate = format(self.rate, '.2f') + ' kiB/s'
                        self.freezeRate = self.rate
                    else:
                        self.rate = self.rate / 1024.0
                        self.rate = format(self.rate, '.2f') + ' MiB/s'
                        self.freezeRate = self.rate

                    if self.restante > 0:
                        self.restante = self.time_read(self.restante, True)
                        self.freezeRestante = self.restante
                    else:
                        self.restante = self.freezeRestante
                else:
                    self.restante = self.freezeRestante
                    self.rate = self.freezeRate

                sector1 = ' Enlace: {0} \n Archivo: {1} \n Tamaño: {2}M \n Conexiones(Threads): {3} \n Estado: {4} \t *Presiona Ctrl+C para pausar o continuar. \n {5} \n '.format(
                                                self.enlace, self.filename,
                                                self.file_size_Megas, self.hilos,
                                                self.StateFile, self.barra
                                                )
                sector2 = '{0} \t Restante: {1}     \t Tasa: {2}'.format(
                                                                    INF, self.restante,
                                                                    self.rate
                                                                    )
                sector2 = self.akua(sector2)

                system('clear')
                print(sector1, sector2)

            except Exception as e:
                logging.debug(unicode(e))
                self.restante = self.freezeRestante
                self.rate = self.freezeRate

            if self.abort:
                return
            while self.pause:
                system('clear')
                print(sector1, sector2)
                if self.abort:
                    return
                sleep(1)
            sleep(0.1)



def main():
    default = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
                'reconect': 100,
                'threads': 3,
                'folder': './',
                'output': '',
                'cookie': '',
                }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--url", help="Enlace de descarga",
        type=str, required=False
        )
    parser.add_argument(
        "-o", "--output", help="Nombre del archivo salida", type=str,
        required=False, default=default['output']
        )
    parser.add_argument(
        "-f", "--folder", help="Carpeta de salida",
        type=str, default=default['folder'],  required=False
        )
    parser.add_argument(
        "-t", "--threads", help="Nº de conexiones concurrentes",
        type=int, default=default['threads'], required=False
        )
    parser.add_argument(
        "-a", "--agent", help="User-Agent del dispositivo",
        type=str, default=default['User-Agent'], required=False
        )
    parser.add_argument(
        "-c", "--cookie", help="Datos de sesion",
        type=str, default=default['cookie'], required=False
        )
    parser.add_argument(
        "-r", "--reconect", help="Nº de reintentos por conexion",
        type=int, default=default['reconect'], required=False
        )
    parser.add_argument(
        "-v", "--version", help="Version del modulo",
        action="store_true"
        )
    parser.add_argument(
        "-p", "--play",
        help="Reproducir video cuando supere el 5 %%, indicar reproductor eje: -p vlc",
        type=str
        )

    args = parser.parse_args()
    color = lambda d: '%s%s %s %s' % (fg(0), bg(85), d, attr('reset'))

    if args.version:
        print(color(__version__))
    elif args.url:
        FreneticDL().download_file(
                                    args.url, args.output,
                                    args.folder, args.cookie,
                                    args.agent, args.reconect,
                                    args.threads, args.play
                                    )
    else:
        print(color('FreneticDL v.%s \n -u   ingrese una URL \n -h   posibles argumentos' % 
            (__version__)))

if __name__ == '__main__':
    main()

