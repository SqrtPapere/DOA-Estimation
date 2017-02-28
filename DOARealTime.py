import time
import serial
import numpy as np
import matplotlib.pyplot as plt
import math
import csv

from timeit import default_timer

# # settings for user
DISPLAY_FLAG = 0
SetSave = 0

live = 1
fileToReadFrom = '3mt_Botto_120.txt'

fileToSaveIn = 'ed-sheeran-50.txt'

while True:
    if live == 1:
        # the number of samples
        sampleNumber = 5000  # numSamples/8

        startProgram = default_timer()

        start = 'a'
        arduino = serial.Serial('/dev/cu.usbmodem1421', 115200, timeout=1)

        time.sleep(2)

        allMics = []
        startSerial = default_timer()
        arduino.write(start.encode('utf-8'))

        firstread = True
        for i in range(sampleNumber):

            if firstread:
                firstread = False
                print('\n' + "start receiving..." + '\n')

            arduinoString = arduino.readline().decode('utf-8')
            dataArray = arduinoString.split(',')
            # print(dataArray)
            allMics.append(dataArray)

        durationSerial = default_timer() - startSerial

        mic0 = [int(row[0]) for row in allMics]
        mic1 = [int(row[1]) for row in allMics]
        mic2 = [int(row[2]) for row in allMics]
        mic3 = [int(row[3]) for row in allMics]
        mic4 = [int(row[4]) for row in allMics]
        mic5 = [int(row[5]) for row in allMics]
        mic6 = [int(row[6]) for row in allMics]
        mic7 = [int(row[7]) for row in allMics]
    else:

        with open(fileToReadFrom) as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

        m0 = rows[0]
        m1 = rows[2]
        m2 = rows[4]
        m3 = rows[6]
        m4 = rows[8]
        m5 = rows[10]
        m6 = rows[12]
        m7 = rows[14]

        del m0[len(m0) - 1]
        del m1[len(m1) - 1]
        del m2[len(m2) - 1]
        del m3[len(m3) - 1]
        del m4[len(m4) - 1]
        del m5[len(m5) - 1]
        del m6[len(m6) - 1]
        del m7[len(m7) - 1]

        mic0 = [int(i) for i in m0]
        mic1 = [int(i) for i in m1]
        mic2 = [int(i) for i in m2]
        mic3 = [int(i) for i in m3]
        mic4 = [int(i) for i in m4]
        mic5 = [int(i) for i in m5]
        mic6 = [int(i) for i in m6]
        mic7 = [int(i) for i in m7]

    if SetSave == 1:

        file = open(fileToSaveIn, "w")

        for item in mic0:
            file.write("%s," % item)
        file.write('\n\n')

        for item in mic1:
            file.write("%s," % item)
        file.write('\n\n')

        for item in mic2:
            file.write("%s," % item)
        file.write('\n\n')

        for item in mic3:
            file.write("%s," % item)
        file.write('\n\n')

        for item in mic4:
            file.write("%s," % item)
        file.write('\n\n')

        for item in mic5:
            file.write("%s," % item)
        file.write('\n\n')

        for item in mic6:
            file.write("%s," % item)
        file.write('\n\n')

        for item in mic7:
            file.write("%s," % item)

        file.close()

        durationSaving = default_timer() - startSaving
        print("Time for Saving: ")
        print(durationSaving)


    # ------------------------------------------------------------------------------

    # Parametri fisici
    c = 343            # velocita suono

    # Parametri array
    M = 8           # numero di sensori
    d = 0.1         # distanza microfoni

    # Parametri calcoli
    N = 64             # numero di punti su cui effettuare la FFT
    J = int(N/2-1)          # numero di bin analizzati in frequenza

    fmax = c/(2*d)            # frequenza massima senza aliasing

    # Metodi di calcolo della media sulle frequenze
    AVG_FLAG = 'arithmetic'   # media aritmetica (sconsigliata per Min-Norm)
    # AVG_FLAG = 'geometric'     # media geometrica

    # ----------------- DEFINIZIONI --------------------

    # Angoli di ricerca (in gradi, spaziatura 1 grado)

    theta = np.arange(1, 180, 0.1)
    theta = theta * np.pi / 180


    SignalMAtrix = np.array([mic0, mic1, mic2, mic3, mic4, mic5, mic6, mic7], 'float')

    SignalMAtrix -= 2**15/5*3.3  # Centramento segnale - (2^16)/2 sta a 5v come la meta ottenibile sta a 3.3v  21627

    K = math.floor(SignalMAtrix.shape[1]/N)  # number of snapshots


    NS = K*N

    num_sources = 1
    fc = 10941     # f_c ADC
    T = 1/fc
    t = np.arange(0, NS)*T

    SignalMAtrix = SignalMAtrix[:, :NS]

    SignalMAtrix = np.flipud(SignalMAtrix)


    array_index = np.arange(-(M-1)/2, M/2)

    # plot data

    if DISPLAY_FLAG == 1:
        plt.plot(mic0, 'black', label="mic0")
        plt.plot(mic1, 'grey', label="mic1")
        plt.plot(mic2, 'r', label="mic2")
        plt.plot(mic3, 'green', label="mic3")
        plt.plot(mic4, 'darkblue', label="mic4")
        plt.plot(mic5, 'dodgerblue', label="mic5")
        plt.plot(mic6, 'gold', label="mic6")
        plt.plot(mic7, 'hotpink', label="mic7")
        plt.legend(bbox_to_anchor=(1.05, 1))
        plt.show()

    # ------- CALCOLO PARAMETRI PER APPLICAZIONE ALGORITMI DOA --------

    w = np.ones(M)

    # Ciclo sugli snapshot e calcolo della DFT, divisione per frequenze

    X = np.zeros(SignalMAtrix.shape, 'complex')

    for k in range(0, K):
        for m in range(0, M):
            s_k = SignalMAtrix[m][k*N:k*N+N]
            S = np.fft.fft(s_k)
            X[m][k:K*N:K] = S

    # calcolo dell'autocorrelazione per ogni frequenza
    R = np.zeros((M, M*N), 'complex')

    Rinv = np.zeros((M, M*N), 'complex')
    PHIn = np.zeros((M, M*N), 'complex')

    for jf in range(0, N):

        S = X[:, jf*K:jf*K+K]
        Rj = np.dot(S, np.conj(S.transpose()))/K

        R[:, jf*M:jf*M+M] = Rj
        # calcolo degli autospazi
        eigenValues, eigenVectors = np.linalg.eigh(Rj)  # autovalori-autovettori
        idx = eigenValues.argsort()[::-1]  # indici autovalori ordinati in ordine decrescente
        eigenValues = eigenValues[idx]  # applicazione ordinamento
        eigenVectors = eigenVectors[:, idx]  # applicazione ordinamento
        L = num_sources
        Un = eigenVectors[:, L:M]  # spazio del rumore
        phin = np.dot(Un, np.conj(Un.transpose()))      # proiettore sullo spazio del rumore
        PHIn[:, jf*M:jf*M+M] = phin

    # plt.plot(PHIn)
    # plt.show()
    # ------- RICERCA DOA TRAMITE STIME SPETTRALI ---------------

    Pth = []
    for th in theta:
        P = []
        for jf in range(1, J+1):
            omega = 2 * np.pi * float(jf) * float(fc) / N
            k = omega/c
            phi = k * d * np.cos(th)  # angolo elettrico (funzione dell'angolo di ricerca e della frequenza f)
            a = np.multiply(w, np.exp(1j * array_index * phi))   # steering vector(multiply per fare elemento per elemento)
            Rj = PHIn[:, jf * M:jf * M + M]
            h = np.dot(a, Rj)
            P.append(1/(np.dot(h, np.conj(a))))
        if AVG_FLAG == 'arithmetic':
            P = np.mean(P)

        Pth.append(P)

    # ----------------- DISPLAY RISULTATI --------------------

    # plot dello stimatore di potenza
    Pth = np.real(Pth)

    if DISPLAY_FLAG == 1:
        plt.plot(Pth, 'black', label="Pth")
        plt.show()

    # calcolo punto di massimo di Pth
    mp = np.argmax(Pth)
    print('Result of MUSIC: ')
    print(mp/10)
    # endProgram = default_timer() - startProgram
    # print(endProgram)



