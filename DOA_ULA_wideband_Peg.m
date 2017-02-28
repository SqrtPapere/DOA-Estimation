clear
% DOA wideband

global c;

% ----------------- PARAMETRI --------------------

% Parametri fisici
c = 343;            % velocita suono

% Parametri array
M = 8;             % numero di sensori
d = 0.1;           % distanza microfoni

% Parametri calcoli
N = 64;             % numero di punti su cui effettuare la FFT
J = N/2-1;          % numero di bin analizzati in frequenza

fmax = c/(2*d);             % frequenza massima senza aliasing

% flag
DISPLAY_FLAG = 1;       % abilita display di grafici (debug)

% Metodo di ricerca DOA
DOA_FLAG = 'MUSIC';        
 
% Metodi di calcolo della media sulle frequenze
AVG_FLAG = 'arithmetic';    % media aritmetica (sconsigliata per Min-Norm)
% AVG_FLAG = 'geometric';     % media geometrica

% ----------------- DEFINIZIONI --------------------

% Angoli di ricerca (in gradi, spaziatura 1 grado)
theta = (1:0.1:179)*pi/180;

% ----------------- LETTURA SEGNALE DI INGRESSO --------------------

% Lettura del segnale in ingresso wideband

% Segnali impulsivi outdoor
 Nw = 2000;
%  x = load('../Data/Outdoor/Botti/3mt_fuori_Botto_30.txt', '-ascii');
%  x = x(:,480:480+Nw);
%  x = load('../Data/Outdoor/Botti/3mt_fuori_Botto_45.txt', '-ascii');
%  x = x(:,480:480+Nw);
%  x = load('../Data/Outdoor/Botti/3mt_fuori_Botto_90.txt', '-ascii');
%  x = x(:,2940:2940+2000);
%  x = load('../Data/Outdoor/Botti/3mt_Botto_120.txt', '-ascii');
 %x = x(:,1150:2700);
 x = load('../Data/Outdoor/Botti/3mt_fuori_Botto_150.txt', '-ascii');
%  x = x(:,2460:2460+Nw);

% x = load('../Data/Outdoor/Botti/doble_source_45_90.txt', '-ascii');
% x = x(:,2200:3000);

% x = load('../Data/Outdoor/Botti/doble_source_75_120.txt', '-ascii');
% x1 = x(:,1:2000);
% x2 = x(:,4400:4700);
% x = horzcat(x1,x2);

% Segnali sinusoidali outdoor
% Nw = 2000;
% x = load('../../Outdoor/3mt_fuori_1000hz_30.txt', '-ascii');
% x = x(:,480:480+Nw);
% x = load('../../Outdoor/3mt_fuori_1000hz_45.txt', '-ascii');
% x = x(:,480:480+Nw);
% x = load('../../Outdoor/3mt_fuori_1000hz_90.txt', '-ascii');
% x = x(:,2940:2940+Nw);
% x = load('../../Outdoor/3mt_fuori_1000hz_120.txt', '-ascii');
% x = x(:,2940:2940+Nw);
% x = load('../../Outdoor/3mt_fuori_1000hz_135.txt', '-ascii');
% x = x(:,1540:1540+Nw);
% x = load('../../Outdoor/3mt_fuori_1000hz_150.txt', '-ascii');
% x = x(:,2460:2460+Nw);

x = x-2^15/5*3.3;     % Centramento segnale - (2^16)/2 sta a 5v come la meta ottenibile t a 3.3v
K = floor(size(x,2)/N);     % numero snapshot di campioni temporali
NS = K*N; 

% asse dei tempi
num_sources = 1;
fc = 10941;     %  frequenza di campionamento dell'ADC
T = 1/fc;  
t = T*(0:NS-1);

% ricampionamento necessario per rimuovere errore introdotto da ADC
x = x(:,1:NS);  
% for k=1:size(x,1)
%     x1 = x(k,:);
%     y1 = resample(x1,8,1,10); % in pratica si riscrive x1 ma con 8 volte campioni in piu
%     y1 = y1(9-k:8:end);  
%     x(k,:) = y1;
% end

x = flipud(x(1:M,1:NS));     % scambio ordine microfoni
array_index = -(M-1)/2:(M-1)/2;    % indici sui sensori

% plot data
plot_line=['r-';'g-';'b-';'k-';'r:';'g:';'b:';'m-']; % colori per plot mic: 7-6-5-4-3-2-1-0 
figure
hold on
for k=1:size(x,1)
    x1 = x(k,:);
    plot(x1,plot_line(k,:));
    set(gca,'FontSize',20)
end

% ------- CALCOLO PARAMETRI PER APPLICAZIONE ALGORITMI DOA --------

w = boxcar(M)'; % finestra rettangolare [1,1,1,1,1,1,1,1]

% Ciclo sugli snapshot e calcolo della DFT, divisione per frequenze
X = zeros(size(x));
for k = 0:K-1
    for m = 1:M
        s_k = x(m,k*N+1:k*N+N);
        S = fft(s_k);
        X(m,k+1:K:K*N) = S;   
    end
end

% calcolo dell'autocorrelazione per ogni frequenza
R = zeros(M,M*N);
Rinv = zeros(M,M*N);
PHIn = zeros(M,M*N);

for jf=0:N-1
    S = X(:,jf*K+1:jf*K+K);
    Rj = S*S'/K;
    
    R(:,jf*M+1:jf*M+M) = Rj;
    
    % calcolo degli autospazi
    [U,D] = eig(Rj); % ricavo autovettori ed autovalori
    ev = diag(D);
    disp(ev);
    [vev,iev] = sort(ev,'descend');
    U = U(:,iev);
    L = num_sources;
    Un = U(:,L+1:M);    % spazio del rumore
    phin = Un*Un';      % proiettore sullo spazio del rumore
    PHIn(:,jf*M+1:jf*M+M) = phin;
    
end
figure, plot(real(PHIn));
% ------- RICERCA DOA TRAMITE STIME SPETTRALI ---------------

Pth = [];
for th = theta
    P = [];
    for jf = 1:J
        omega = 2*pi*jf*fc/N;
        k = omega/c;
        phi = k*d*cos(th);  % angolo elettrico (funzione dell'angolo di ricerca e della frequenza f)
        a = w.*exp(1j*array_index*phi); % steering vector
        Rj = PHIn(:,jf*M+1:jf*M+M);
        P = [P 1/(a*Rj*a')];
    end
    if strcmp(AVG_FLAG,'arithmetic')
        P = mean(P);
    elseif strcmp(AVG_FLAG,'geometric')
        P = geomean(P);
    end
    Pth = [Pth P];
end

% ----------------- DISPLAY RISULTATI --------------------

% plot dello stimatore di potenza (metodi ad analisi spettrale)

Pth = real(Pth);
figure, plot(theta*180/pi,Pth, 'LineWidth',2)
set(gca,'FontSize',20)
xlabel('Angolo di arrivo (in gradi)')
ylabel('Potenza')

% calcolo punto di massimo di Pth
[mp,np] = max(Pth);
% disp('Angolo di arrivo MISURATO relativo al max picco spettrale:');
disp(np/10);

