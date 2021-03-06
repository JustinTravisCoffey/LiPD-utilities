

% function pages2k_phase2_db_synopsis(vers,options)
%  INPUT:   vers (version of the database, string)
%           (optional) export. If true, exports figures to pdf. If not,
%           simply prints them to screen. [default =0]
%
% WHAT: plot space time map of TS data 
%
% WHO/WHEN started Dec 5 2014 by Julien Emile-Geay (USC)
%Adapted for LiPD Utilities by Nick McKay (NAU)
inset = 0;
% process options
% if nargin < 2
%     options.export = 0;
% end
age = [];
% load data and packages% if nargin < 2
%     options.export = 0;
% end

%addpath(genpath('../utilities'));
%load(['../../data/proxy_db/pages2kTSv' vers '_unpack.mat'])
FontName = 'Helvetica';
set(0,'defaultAxesFontName', FontName)
set(0,'defaultTextFontName', FontName)
style_t = {'FontName',FontName,'Fontweight','Bold','Fontsize',16};
style_l = {'FontName',FontName};
%figpath = '../../figs/synopsis/';


TSall = TS;
values = {TS.paleoData_values};
cellcol = find(cellfun(@iscell,{TS.paleoData_values}));
values(cellcol)=repmat({NaN},length(cellcol),1);
allnan = find(cellfun(@(x) all(isnan(x)),values));
good = setdiff(1:length(TSall),allnan);
TS=TSall(good);

notCell = find(~cellfun(@iscell,{TS.age}) & ~cellfun(@isempty,{TS.age}));
check = find(cellfun(@iscell,{TS.age}));


if length(notCell)>1
TS=TS(notCell);
end
minage = num2cell(cellfun(@nanmin,{TS.age}));
maxage = num2cell(cellfun(@nanmax,{TS.age}));

[TS.minage] = minage{:};
[TS.maxage] = maxage{:};



%pull relevant data from TS
TS = convertNamesTS(TS,'archiveType');
archive={TS.archiveType}';

age=1:2000;
nr=length(TS);
ageMin={TS.minage}';
emptyageMin = find(cellfun(@isempty,ageMin));
ageMin(emptyageMin)=repmat({NaN},length(emptyageMin),1);
ageMin=cell2mat(ageMin);

ageMax={TS.maxage}';
emptyageMax = find(cellfun(@isempty,ageMax));
ageMax(emptyageMax)=repmat({NaN},length(emptyageMax),1);
ageMax=cell2mat(ageMax);

ageMax(ageMax > 2000) = 2000;
ageMin(ageMin < 000) = 000;
ageMin(ageMin > 2000) = 2000;
ageMax(ageMax < 000) = 000;


p_lon = nan(length(TS),1);
p_lat=p_lon;
goodLon = find(~cellfun(@isempty,{TS.geo_meanLon}));
goodLat = find(~cellfun(@isempty,{TS.geo_meanLat}));

p_lon(goodLon)=cell2mat({TS.geo_meanLon}');
p_lat(goodLat)=cell2mat({TS.geo_meanLat}');

medRes = calculateMedianResolutionTS(TS,'year',0,2000);

%%
% extract archive types and assign colors
% =========================================
% fix inconsistencies
%archive = strrep(archive,'Tree Ring','tree');
%archive = strrep(archive,'documents','historic');
%archive = strrep(archive,'historical','historic');
%archive = strrep(archive,'lake','Lake sediment');
%archive(strcmp('ice',archive))={'ice core'};
%archive(cellfun(@isempty,archive))={'n/a'};
% Graphical Attributes of each proxy type
archiveType = unique(lower(archive)); na = length(archiveType);

Graph{1,1}=rgb('DarkOrange');  Graph{1,2}= 'o'; %coral
Graph{2,1}=rgb('LightSkyBlue');Graph{2,2}= 'd'; %glacier ice
Graph{3,1}=rgb('SaddleBrown'); Graph{3,2}= 's'; %Marine Sediment
Graph{4,1}=rgb('Red');         Graph{4,2}= 'o';  %sclero sponge
Graph{5,1}=rgb('RoyalBlue');   Graph{5,2}= 's'; %Lake sediment
Graph{6,1}=rgb('Black');       Graph{6,2}= 'p'; %documents
Graph{7,1}=rgb('DarkKhaki');   Graph{7,2}= 'h'; 
Graph{8,1}=rgb('DeepSkyBlue'); Graph{8,2}= 's'; 
Graph{9,1}=rgb('Gold');        Graph{9,2}= 's'; %peat
Graph{10,1}=rgb('DeepPink');   Graph{10,2}= 'd'; %speleothems
Graph{11,1}=rgb('LimeGreen');  Graph{11,2}= '^'; %tree

if na>size(Graph,1)
    error('More than 11 archive types. Beyond current functionality')
end

%use specific archives

Graph=Graph([2 5 3 9 10 11],:);



% DEFINE TIME AXIS AND AVAILABILITY
% avail = ~isnan(proxy);
ny = length(age);

avail = NaN(ny,nr);

p_code = nan(nr,1);
for r = 1:nr
    % define proxy code
    s = strfind(archiveType,lower(archive{r}));
    p_code(r) =  find(~cellfun('isempty', s), 1 ); % number between 1 and na
    avail(ismember(age,[floor(ageMin(r)):ceil(ageMax(r))]),r)=1;
end

% define edge color (black except for hybrids)
edgec = cell(nr,1);
edgec(1:nr) = {'none'};%{rgb('Black')};
if na>=6
edgec(p_code == 6) = {Graph{6,1}};
end

nproxy = zeros(ny,na); pind = zeros(na,1);
for a = 1:na % loop over archive types
    nproxy(:,a) = sum(~isnan(avail(:,p_code == a)),2);
    pind(a) = find(p_code == a,1,'first');
    nArch(a)   = sum(p_code == a);
    leg_lbl{a} = [archiveType{a} ' (' int2str(nArch(a)) ')'];
    %disp(leg_lbl{a})
end
%%
% =============
% PLOT SPACETIME COVERAGE
% =============
n1000 = ceil(sum(nproxy(age == 1000,:))/10)*10;
ns    = length(unique({TS.dataSetName})); % # of sites
%versl = strrep(vers,'_','.');
fig('OnsetSpaceTime'), clf
orient landscape
set(gcf,'PaperPositionMode','auto')
set(gcf, 'Position', [440   144   896   654])
% plot spatial distribution
hmap=axes('Position', [.0 0.45 0.45 0.5]);
m_proj('stereographic','lat',90,'long',45,'radius',35,'rotangle',45)
m_coast('patch',[.9 .9 .9]);
m_grid('xtick',6,'ytick',[60 70 80],'xticklabel',[ ],'xlabeldir','middle', 'fontsize',4,'fontname',FontName);
% loop over records
for r = 1:nr
    h(r) = m_line(p_lon(r),p_lat(r),'marker',Graph{p_code(r),2},'MarkerEdgeColor',edgec{r},'MarkerFaceColor',Graph{p_code(r),1},'linewidth',[1],'MarkerSize',[7],'linestyle','none');
end
text(-2,1.75,[int2str(nr) , ' records from ', int2str(ns), ' sites'],style_t{:});
title('a) Archive Type',style_t{:});



% TEMPORAL AVAILABILITY
hstack=axes('Position', [0.1 0.1 0.8 0.29]);
cmap=cell2mat(Graph(:,1));
colormap(hstack,cmap);
area(age,nproxy,'EdgeColor','w'), set(gca,'YAxisLocation','Right');
xlim([0 2000])
set(gca,'XDir','reverse')
fancyplot_deco('','age (yr BP)','# timeseries',14,'Helvetica');
title('c) Temporal Availability',style_t{:})


% legend
hl = legend(h(pind),leg_lbl,'location',[.34 .75 .1 .2],style_l{:});
set(hl, 'FontName', FontName,'box','on');


%plot resolution
hmap2=axes('Position', [.45 0.45 0.45 0.5]);
m_proj('stereographic','lat',90,'long',45,'radius',35,'rotangle',45)
m_coast('patch',[.9 .9 .9]);
m_grid('xtick',6,'ytick',[60 70 80],'xticklabel',[ ],'xlabeldir','middle', 'fontsize',4,'fontname',FontName);
scheme = 'RdYlBu'; cx = [1,500];
nc = 11; % number of color contours
colR = t2c_brewer(medRes,nc,scheme,cx);
% loop over records
for r = 1:nr
    h(r) = m_line(p_lon(r),p_lat(r),'marker',Graph{p_code(r),2},'MarkerEdgeColor','none','MarkerFaceColor',colR(r,:),'linewidth',0.5,'MarkerSize',7,'linestyle',':');
end


% colorbar
ogSize = get(gca, 'Position'); caxis(cx)
hc = colorbar(); dtm = 1/12;
ytl = [1, 100, 200, 300, 400, 500]';
yt = (ytl);
pos = get(hc,'Position');
set(hc,'YTick',yt,'YLim',cx,'Position',[pos(1)+0.05,pos(2),pos(3),pos(4)]);
set(hc,'YTickLabel',rats(ytl),'FontName','Helvetica');
ylabel(hc,'Median Resolution (yr)','FontName','Helvetica','FontName','Helvetica','FontSize',round(.86*14));
set(gca,'Position',ogSize);
title('b) Resolution',style_t{:});
hold on



%%


%pause; % manually adjust the size of the figure
   %figpath = [strrep(userpath,':','/') 'tempfigs/'];
   fname = ['~/Dropbox/AHT/OnsetPaper/Manuscript/Figures/Onset_spacetime.pdf'];
   export_fig([fname]);
   %hepta_figprint(['../../figs/synopsis/PAGES2K_phase2_' vers '_spacetime']);
   %saveFigure([figpath fname '_saveFigure.pdf']); %'painters', true
   %plot2svg([figpath fname '.svg']);
   %print([figpath fname],'-depsc','-r300','-cmyk')

