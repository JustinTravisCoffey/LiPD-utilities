%collapseTS
%converts TS (LiPD TS object) structure to D (Lipd Hierarchical Object) structure
clear
load ~/Dropbox/Pages2kPhase2/p2kDatabaseWithNewTSIDs.mat TS


%update TS naming to LiPD
%remove dataSetName field for now
TS=rmfield(TS,'dataSetName');

%HACKS
TS(4504).pubYear=2005;
TS(4508).pubYear=2007;
TS(4579).pubYear=2002;
TS(4579).pub_year=2002;
TS(4646).pubYear=2011;
TS(4646).pub_year=2011;

TS=renameTS(TS,1); %removing entries that aren't in the table

%hold onto dataset names
oldDataSetName={TS.dataSetName}';

%update from google
run('~/Dropbox/Pages2kPhase2/updateTSfromGoogle.m');
TS=renameTS(TS,1); %removing entries that aren't in the table
newDataSetName={TS.dataSetName}';
%handle dataset naming.
%
uNames=unique(oldDataSetName);
for u=1:length(uNames)
    %find all oldNames
    oi=find(strcmp(uNames{u},oldDataSetName));
    %is there a new name for all of those?
    ne=find(strcmpi(uNames{u},newDataSetName(oi)));
    if length(ne)<length(oi)%if any are different
        nf=setdiff(oi,oi(ne));
        ne=oi(ne);
        if length(nf>0)%replace all the old names with new names
            for n=1:length(ne)
            newDataSetName{ne(n)}=newDataSetName{nf(1)};
            end
        end
    end
end
%replace any remaining empty new names with oldnames
    ne=find(cellfun(@isempty,newDataSetName));
newDataSetName(ne)=oldDataSetName(ne);

newName=strcat({TS.geo_pages2kRegion}',{'-'},newDataSetName);
[TS.dataSetName]=newName{:};
%%
%intialize some variables
lastParamName='dum';
lastPDName='dum';
lastDataSetName='dum';


%create a LiPD object for every unique dataSetName
udsn=unique({TS.dataSetName}');

for i=1:length(udsn)
    %find TS entries that match that unique Name
    fts=find(strcmp(udsn{i},{TS.dataSetName}'));
    
    for f=1:length(fts) %make a paleoDataTable entry for each TS
        T=TS(fts(f));
        T=removeEmptyStructureFields(T);
        fT=fieldnames(T);
        
        %base level
        %all the fields that don't have underscores (except year and age)
        b=find(cellfun(@isempty,(strfind(fT,'_'))));
        yi=find(strcmpi('year',fT));
        ai=find(strcmpi('age',fT));
        yai=union(ai,yi);
        b=setdiff(b,yai);
        
        for bi=1:length(b)
            Dnew.(matlab.lang.makeValidName(udsn{i})).(fT{b(bi)})=T.(fT{b(bi)});
        end
        
        %funding
        fun=find(strncmp('funding_',fT,8));
        if numel(fun)>0
            Dnew.(matlab.lang.makeValidName(udsn{i})).funding=cell(1,1); %assign cell to funding
            for fin=1:length(fun)
                funVarName=fT{fun(fin)};
                fundNum=str2num(funVarName(8:(strfind(funVarName,'_')-1)));
                Dnew.(matlab.lang.makeValidName(udsn{i})).funding{fundNum}.(funVarName(strfind(funVarName,'_')+1:end))=...
                    T.(fT{fun(fin)});
            end
        end
        
        
        %pub
        if f==1
            Dnew.(matlab.lang.makeValidName(udsn{i})).pub=cell(1,1); %assign cell to pub
        end
        p=find(strncmp('pub',fT,3));
        for pin=1:length(p)
            pubVarName=fT{p(pin)};
            pubNum=str2num(pubVarName(4:(strfind(pubVarName,'_')-1)));
            Dnew.(matlab.lang.makeValidName(udsn{i})).pub{pubNum}.(pubVarName(strfind(pubVarName,'_')+1:end))=...
                T.(fT{p(pin)});
        end
        
        %geo
        if f==1
            Dnew.(matlab.lang.makeValidName(udsn{i})).geo=struct; %assign geo to structure
        end
        g=find(strncmp('geo_',fT,4));
        
        for gin=1:length(g)
            geoVarName=fT{g(gin)};
            
            Dnew.(matlab.lang.makeValidName(udsn{i})).geo.(geoVarName(strfind(geoVarName,'_')+1:end))=...
                T.(fT{g(gin)});
        end
        
        
        
        %paleoData
        if f==1
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData=struct; %assign paleoData to structure
        end
        pd=find(strncmp('paleoData_',fT,10));
        
        %get or create the name of the relevant paleodata table
        if isfield(T,'paleoData_tableName')

                pdName=T.paleoData_tableName;
        else
            pdName='s1';
            T.paleoData_tableName='s1';
            TS(fts(f)).paleoData_tableName=pdName;
        end
        
        %check if this name has been used before - make sure entries are same
        %find all other TS with this dataSetName and paleoData_tableName
        samei=find(strcmp(udsn{i},{TS.dataSetName}') & strcmp(T.paleoData_tableName,{TS.paleoData_tableName}'));
        if length(samei)>1
            clear dll
            for dl=1:length(samei)
                dll(dl)=length(TS(samei(dl)).paleoData_values);
            end
        
        %if they're not all thesame length, rename all tables including the length    
            if length(unique(dll))>1
                                pdName=['pdt' num2str(length(T.paleoData_values))];
            end
        end
                
        
        %get variablename name
        variableName=matlab.lang.makeValidName(T.paleoData_variableName);
        
        for pdin=1:length(pd)
            pdVarName=fT{pd(pdin)};
            
            %add in parameter
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).(variableName).(pdVarName(strfind(pdVarName,'_')+1:end))=...
                T.(fT{pd(pdin)});
            
            %store last param name and last paleodata name for reference
            lastParamName=variableName;
            lastPDName=pdName;
            lastDataSetName=matlab.lang.makeValidName(udsn{i});
            
        end
        
        %add year as a column
        yearFlag=0;
        if any(strcmp('year',fT))
            if length(T.year) == length(T.paleoData_values)
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).year.values=T.year;
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).year.units='AD';
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).year.description='Year AD';
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).year.variableName='year';
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).year.dataType='float';
            yearFlag=1;
            end
        end
        %add age as column
        ageFlag=0;
        if any(strcmp('age',fT))
            %don't add age if it's a different length than the data
            if length(T.age) == length(T.paleoData_values)
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).age.values=T.age;
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).age.units='BP';
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).age.description='Years before present (1950) BP';
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).age.variableName='age';
            Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).age.dataType='float';
            ageFlag=1;
            end
        end
        if ~ageFlag && ~yearFlag
            error('no age or year data. The linearity (and existence) of time are necessary assumptions in the LiPD framework | a likely problem is that the length of the data does not match the length of the year and/or age vectors')
        end
        
        %check for climate interpretation
        if any(strncmp('climateInterpretation_',fT,22))
            ci=find(strncmp('climateInterpretation_',fT,22));
            for cin=1:length(ci)
                ciVarName=fT{ci(cin)};
                
                %add in parameter
                Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).(variableName).climateInterpretation.(ciVarName(strfind(ciVarName,'_')+1:end))=...
                    T.(fT{ci(cin)});
            end
        end
        
        %check for calibration
        if any(strncmp('calibration_',fT,12))
            cai=find(strncmp('calibration_',fT,12));
            for cain=1:length(cai)
                caiVarName=fT{cai(cain)};
                
                %add in parameter
                Dnew.(matlab.lang.makeValidName(udsn{i})).paleoData.(pdName).(variableName).calibration.(caiVarName(strfind(caiVarName,'_')+1:end))=...
                    T.(fT{cai(cain)});
            end
        end
        
    end
    
end
%%
dnames=fieldnames(Dnew);
for d=1:length(dnames)
   writeLiPD(Dnew.(dnames{d}),1,'~/Dropbox/LiPD/library/'); 
end