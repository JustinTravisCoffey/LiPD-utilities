# -*- coding: utf-8 -*-
import json
import requests
import os

from .loggers import create_logger

logger_validator_api = create_logger('validator_api')


def get_validator_format(data_json, data_csv, filenames):
    """
    Format the LIPD data in the layout that the Lipd.net validator accepts.
    Example of one _file metadata. _file_list will contain 1 or more _file's
    _file = {
        "type": "bagit/json/csv",
        "filenameFull": /path/to/filename.txt,
        "filenameShort": filename.txt,
        "data": "",
        "pretty": ""
    }

    :param dict data_json: Metadata
    :param dict data_csv: CSV data
    :param list filenames: All files found in LiPD archive
    :return list: Validator-formatted data
    """
    # Store the metadata for each file in the _file_list
    _file_lst = []
    # Loop for each filename
    for filename in filenames:
        # Create a blank template
        _file = {"type": "", "filenameFull": "", "filenameShort": "", "data": "", "pretty": ""}
        # filename, no path prefix
        _short = os.path.basename(filename)
        # Bagit files
        if filename.endswith(".txt"):
            _file = {"type": "bagit", "filenameFull": filename, "filenameShort": _short}
        # JSONLD files
        elif filename.endswith(".jsonld"):
            _file = {"type": "json", "filenameFull": filename, "filenameShort": _short, "data": data_json}

        # CSV files
        elif filename.endswith(".csv"):
            _cols = len(data_csv[os.path.basename(filename)])
            _rows = 0
            for k, v in data_csv[_short].items():
                _rows = len(v)
                break
            _file = {"type": "csv", "filenameFull": filename, "filenameShort": _short,
                     "data": {"cols": _cols, "rows": _rows}}
        _file_lst.append(_file)

    return _file_lst


def create_detailed_results(data):
    """
    """
    string = ""
    # Validation Response output
    # string += "VALIDATION RESPONSE\n"
    string += "STATUS: {}\n".format(data["status"])
    if data["feedback"]:
        string += "WARNINGS: {}\n".format(len(data["feedback"]["wrnMsgs"]))
        # Loop through and output the Warnings
        for msg in data["feedback"]["wrnMsgs"]:
            string += "- {}\n".format(msg)
        string += "ERRORS: {}\n".format(len(data["feedback"]["errMsgs"]))
        # Loop through and output the Errors
        for msg in data["feedback"]["errMsgs"]:
            string += "- {}\n".format(msg)
    return string


def display_results(data, detailed=False):
    """
    Display the results from the validator in a brief or detailed way.
    :param dict data: Results, sorted by dataset name
    :param bool detailed: Detailed results on or off
    :return none:
    """
    # print("\nVALIDATOR RESULTS")
    # print("======================\n")

    if not detailed:
        print('FILENAME......................................... STATUS..........')

    for lipd in data:
        try:
            if detailed:
                print("\n{}".format(lipd["filename"]))
                print(create_detailed_results(lipd))
            else:
                print("{:<50}{}".format(lipd["filename"], lipd["status"]))
        except Exception as e:
            logger_validator_api.debug("display_results: Exception: {}".format(e))
            print("skipping...")

    return


def get_validator_results(data):
    """
    Send LiPD data to the Lipd.net validator and get the results back.
    :param data:
    :return:
    """
    # results = {"detailed": "", "raw": {}, "status": "", "filename":""}
    results = []
    for file in data:
        # Add this single results to the growing list of results.
        result = _call_validator_api(file)
        results.append(result)

    return results


def _get_failed_filename(file):
    """
    File has failed JSON dump. Find the filename so we can notify the user.
    :param file:
    :return:
    """
    _filename = "unknown file"
    try:
        _filename = file[0]["filenameFull"].split("/")[0] + ".lpd"
    except IndexError:
        pass
    return _filename


def _call_validator_api(data):
    """
    Single call to the lipd.net validator API
    Returns data in format: {"dat": <dict>, "feedback": <dict>, "filename": "", "status": ""}

    :param list data: Prepared payload. JSON dumped data. Single or batch.
    :return list: Validator results
    """
    _filename = _get_failed_filename(data)

    try:
        # Contact server and send LiPD metadata as the payload
        # print("Sending request to LiPD.net validator...\n")
        data = json.dumps(data)

        # The payload that is going to be sent with the JSON request
        payload = {'json_payload': data, 'apikey': 'YOUR_API_KEY_HERE'}
        # Development Link
        # response = requests.post('http://localhost:3000/api/validator', data=payload)

        # Production Link
        response = requests.post('http://www.lipd.net/api/validator', data=payload)

        # For an example of the JSON Response, reference the "sample_data_response" below

        # Convert JSON string into a Python dictionary
        # print("Converting response to json...\n")
        result = json.loads(response.text)

    except TypeError as e:
        logger_validator_api.warning("get_validator_results: TypeError: {}".format(e))
        result = {"dat": {}, "feedback": {}, "filename": _filename, "status": "DECODE ERROR, FOREIGN SYMBOLS OR CHARACTERS"}
    except requests.exceptions.ConnectionError as e:
        logger_validator_api.warning("get_validator_results: ConnectionError: {}".format(e))
        result = {"dat": {}, "feedback": {}, "filename": _filename, "status": "UNABLE TO REACH SERVER"}
    except Exception as e:
        logger_validator_api.debug("get_validator_results: Exception: {}".format(e))
        result = {"dat": {}, "feedback": {}, "filename": _filename, "status": "ERROR BEFORE VALIDATION"}
    if not result:
        result = {"dat": {}, "feedback": {}, "filename": _filename, "status": "EMPTY RESPONSE"}

    return result

# Validator Format
# This is a list of lists
# Each request contains one array
# That main array contains one array per LiPD archive
# Each LiPD archive array contains one JSON object per file inside of the LiPD archive (3 bagit txt, 1+ jsonld, 1+ csv)
sample_data_request = [

    [
        {
            "type": "bagit",
            "filenameFull": "MD98-2170.Stott.2004/bag-info.txt",
            "filenameShort": "bag-info.txt",
            "data": "",
            # "pretty": "\"\""
        },
        {
            "type": "bagit",
            "filenameFull": "MD98-2170.Stott.2004/bagit.txt",
            "filenameShort": "bagit.txt",
            "data": "BagIt-Version: 0.96\nTag-File-Character-Encoding: UTF-8\n",
            # "pretty": "\"BagIt-Version: 0.96\\nTag-File-Character-Encoding: UTF-8\\n\""
        },
        {
            "type": "bagit",
            "filenameFull": "MD98-2170.Stott.2004/manifest-md5.txt",
            "filenameShort": "manifest-md5.txt",
            "data": "36bc011ad51cb607b4c5387262f51320 data/MD98-2170.Stott.2004.chron1measurement1.csv\nee0a2f9444dee56be93d87c7c30114a2 data/MD98-2170.Stott.2004.jsonld\n5d6b9d190dac29878874a92a0f616169 data/MD98-2170.Stott.2004.paleo1measurement1.csv\n",
            # "pretty": "\"36bc011ad51cb607b4c5387262f51320 data/MD98-2170.Stott.2004.chron1measurement1.csv\\nee0a2f9444dee56be93d87c7c30114a2 data/MD98-2170.Stott.2004.jsonld\\n5d6b9d190dac29878874a92a0f616169 data/MD98-2170.Stott.2004.paleo1measurement1.csv\\n\""
        },
        {
            "type": "bagit",
            "filenameFull": "MD98-2170.Stott.2004/tagmanifest-md5.txt",
            "filenameShort": "tagmanifest-md5.txt",
            "data": "d41d8cd98f00b204e9800998ecf8427e bag-info.txt\nace0ef9419c8edbe164a888d4e4ab7ee bagit.txt\n6754ca6beb4812de50cec58d8b4b2ef9 manifest-md5.txt\n",
            # "pretty": "\"d41d8cd98f00b204e9800998ecf8427e bag-info.txt\\nace0ef9419c8edbe164a888d4e4ab7ee bagit.txt\\n6754ca6beb4812de50cec58d8b4b2ef9 manifest-md5.txt\\n\""
        },
        {
            "type": "csv",
            "filenameFull": "MD98-2170.Stott.2004/data/MD98-2170.Stott.2004.chron1measurement1.csv",
            "filenameShort": "MD98-2170.Stott.2004.chron1measurement1.csv",
            "data": {
                "data": [
                    [
                        "7.0",
                        "OS-38364",
                        "G. sacculifer",
                        "2370.0",
                        "25.0"
                    ],
                    [
                        "102.0",
                        "OS-38365",
                        "G. sacculifer",
                        "8520.0",
                        "40.0"
                    ],
                    [
                        "200.0",
                        "OS-38366",
                        "G. sacculifer",
                        "6900.0",
                        "35.0"
                    ],
                    [
                        "300.0",
                        "OS-38367",
                        "G. sacculifer",
                        "9710.0",
                        "45.0"
                    ],
                    [
                        "401.0",
                        "OS-54863",
                        "G. sacculifer",
                        "14900.0",
                        "90.0"
                    ],
                    [
                        "427.0",
                        "OS-54864",
                        "G. sacculifer",
                        "15450.0",
                        "80.0"
                    ],
                    [
                        ""
                    ]
                ],
                "errors": [],
                "meta": {
                    "delimiter": ",",
                    "linebreak": "\r\n",
                    "cursor": 252
                },
                "rows": 7,
                "cols": 5,
                "delimiter": ","
            },
            # "pretty": "{\n  \"data\": [\n    [\n      \"7.0\",\n      \"OS-38364\",\n      \"G. sacculifer\",\n      \"2370.0\",\n      \"25.0\"\n    ],\n    [\n      \"102.0\",\n      \"OS-38365\",\n      \"G. sacculifer\",\n      \"8520.0\",\n      \"40.0\"\n    ],\n    [\n      \"200.0\",\n      \"OS-38366\",\n      \"G. sacculifer\",\n      \"6900.0\",\n      \"35.0\"\n    ],\n    [\n      \"300.0\",\n      \"OS-38367\",\n      \"G. sacculifer\",\n      \"9710.0\",\n      \"45.0\"\n    ],\n    [\n      \"401.0\",\n      \"OS-54863\",\n      \"G. sacculifer\",\n      \"14900.0\",\n      \"90.0\"\n    ],\n    [\n      \"427.0\",\n      \"OS-54864\",\n      \"G. sacculifer\",\n      \"15450.0\",\n      \"80.0\"\n    ],\n    [\n      \"\"\n    ]\n  ],\n  \"errors\": [],\n  \"meta\": {\n    \"delimiter\": \",\",\n    \"linebreak\": \"\\r\\n\",\n    \"aborted\": false,\n    \"truncated\": false,\n    \"cursor\": 252\n  },\n  \"rows\": 7,\n  \"cols\": 5,\n  \"delimiter\": \",\"\n}"
        },
        {
            "type": "json",
            "filenameFull": "MD98-2170.Stott.2004/data/MD98-2170.Stott.2004.jsonld",
            "filenameShort": "MD98-2170.Stott.2004.jsonld",
            "data": {
                "archiveType": "marine sediment",
                "geo": {
                    "geometry": {
                        "coordinates": [
                            125.39,
                            -10.59,
                            -832
                        ],
                        "type": "Point"
                    },
                    "properties": {
                        "siteName": "MD98-2170"
                    },
                    "type": "Feature"
                },
                "investigator": [
                    {
                        "name": "L.D. Stott"
                    },
                    {
                        "name": "K.G. Cannariato"
                    },
                    {
                        "name": "R.C. Thunell"
                    },
                    {
                        "name": "G.H. Haug"
                    },
                    {
                        "name": "A. Koutavas"
                    },
                    {
                        "name": "S.P. Lund"
                    }
                ],
                "description": "Western Tropical Pacific Holocene Sea Surface Temperature and Salinity Reconstructions. delta O18 PDB (Globigerinoides ruber); Magnesium/Calcium ratio (Globigerinoides ruber); Sea Surface Temperature (C); delta O18 SMOW (water); radiocarbon years before 1950AD",
                "chronData": [
                    {
                        "chronMeasurementTable": [
                            {
                                "chronDataTableName": "chron1measurement1",
                                "filename": "MD98-2170.Stott.2004.chron1measurement1.csv",
                                "columns": [
                                    {
                                        "number": "1",
                                        "variableName": "depth",
                                        "variableType": "measured"
                                    },
                                    {
                                        "number": "2",
                                        "variableName": "labcode",
                                        "takenAtDepth": {
                                            "foundInTable": "MD98-2170.Stott.2004.chron1measurement1",
                                            "hasColumnNumber": "1",
                                            "name": "depth"
                                        },
                                        "variableType": "measured"
                                    },
                                    {
                                        "number": "3",
                                        "variableName": "mat",
                                        "takenAtDepth": {
                                            "foundInTable": "MD98-2170.Stott.2004.chron1measurement1",
                                            "hasColumnNumber": "1",
                                            "name": "depth"
                                        },
                                        "variableType": "measured"
                                    },
                                    {
                                        "number": "4",
                                        "units": "yr BP",
                                        "measuredOn": {
                                            "archiveName": "MD98-2170",
                                            "sensingWith": "Globigerinoides sacculifer"
                                        },
                                        "variableName": "age14c",
                                        "onProxyObservationProperty": "Radiocarbon",
                                        "takenAtDepth": {
                                            "foundInTable": "MD98-2170.Stott.2004.chron1measurement1",
                                            "hasColumnNumber": "1",
                                            "name": "depth"
                                        },
                                        "variableType": "measured",
                                        "uncertainty": 0,
                                        "hasUnits": "yr BP",
                                        "uncertaintyLevel": "1 sigma"
                                    },
                                    {
                                        "number": "5",
                                        "variableName": "age14cuncertainty",
                                        "takenAtDepth": ".depth",
                                        "variableType": "measured"
                                    }
                                ],
                                "missingValue": "NaN"
                            }
                        ]
                    }
                ],
                "paleoData": [
                    {
                        "paleoMeasurementTable": [
                            {
                                "filename": "MD98-2170.Stott.2004.paleo1measurement1.csv",
                                "columns": [
                                    {
                                        "description": "depth (cm)",
                                        "number": "1",
                                        "units": "cm",
                                        "variableName": "depth",
                                        "variableType": "measured"
                                    },
                                    {
                                        "description": "age yr BP",
                                        "number": "2",
                                        "missingValue": "-999",
                                        "units": "yr BP",
                                        "max": 14575.9,
                                        "min": 0,
                                        "variableName": "age",
                                        "onInferredVariableProperty": "Age",
                                        "takenAtDepth": {
                                            "description": "depth (cm)",
                                            "foundInTable": "MD98-2170.Stott.2004.paleo1measurement1",
                                            "hasColumnNumber": "1",
                                            "hasUnits": "cm",
                                            "name": "depth"
                                        },
                                        "variableType": "inferred"
                                    },
                                    {
                                        "description": "d18O PDB",
                                        "number": "3",
                                        "missingValue": "-999",
                                        "units": "per mil",
                                        "measuredOn": {
                                            "archiveName": "MD98-2170",
                                            "sensingWith": {
                                                "sensorGenus": "Globigerinoides",
                                                "sensorSpecies": "ruber"
                                            }
                                        },
                                        "measurementMaterial": "Globigerinoides ruber",
                                        "variableName": "d18o",
                                        "onProxyObservationProperty": "D18O",
                                        "measurementStandard": "VPDB",
                                        "takenAtDepth": {
                                            "description": "depth (cm)",
                                            "foundInTable": "MD98-2170.Stott.2004.paleo1measurement1",
                                            "hasColumnNumber": "1",
                                            "hasUnits": "cm",
                                            "name": "depth"
                                        },
                                        "variableType": "measured"
                                    },
                                    {
                                        "description": "d18O SMOW",
                                        "number": "4",
                                        "missingValue": "-999",
                                        "units": "per mil SMOW",
                                        "measurementMaterial": "water",
                                        "variableName": "d18ow",
                                        "onInferredVariableProperty": "D18Osw",
                                        "takenAtDepth": {
                                            "description": "depth (cm)",
                                            "foundInTable": "MD98-2170.Stott.2004.paleo1measurement1",
                                            "hasColumnNumber": "1",
                                            "hasUnits": "cm",
                                            "name": "depth"
                                        },
                                        "variableType": "inferred"
                                    },
                                    {
                                        "description": "Mg/Ca ratio",
                                        "number": "5",
                                        "missingValue": "-999",
                                        "units": "mmol/mol",
                                        "measuredOn": {
                                            "archiveName": "MD98-2170",
                                            "sensingWith": {
                                                "sensorGenus": "Globigerinoides",
                                                "sensorSpecies": "ruber"
                                            }
                                        },
                                        "variableName": "mg",
                                        "onProxyObservationProperty": "Mg/Ca",
                                        "takenAtDepth": {
                                            "description": "depth (cm)",
                                            "foundInTable": "MD98-2170.Stott.2004.paleo1measurement1",
                                            "hasColumnNumber": "1",
                                            "hasUnits": "cm",
                                            "name": "depth"
                                        },
                                        "variableType": "measured"
                                    },
                                    {
                                        "description": "Mg/Ca sea surface temperature",
                                        "number": "6",
                                        "missingValue": "-999",
                                        "units": "deg C",
                                        "variableName": "sst",
                                        "onInferredVariableProperty": "SST",
                                        "takenAtDepth": {
                                            "description": "depth (cm)",
                                            "foundInTable": "MD98-2170.Stott.2004.paleo1measurement1",
                                            "hasColumnNumber": "1",
                                            "hasUnits": "cm",
                                            "name": "depth"
                                        },
                                        "variableType": "inferred"
                                    }
                                ],
                                "missingValue": "-999",
                                "paleoDataTableName": "paleo1measurement1"
                            }
                        ]
                    }
                ],
                "liPDVersion": 1.2,
                "dataSetName": "MD98-2170.Stott.2004",
                "proxy": "Paleoceanography",
                "pub": [
                    {
                        "abstract": "In the present-day climate, surface water salinities are low in the western tropical Pacific Ocean and increase towards the eastern part of the basin. The salinity of surface waters in the tropical Pacific Ocean is thought to be controlled by a combination of atmospheric convection, precipitation, evaporation and ocean dynamics, and on interannual timescales significant variability is associated with the El Niņo/Southern Oscillation cycles. However, little is known about the variability of the coupled ocean-atmosphere system on timescales of centuries to millennia. Here we combine oxygen isotope and Mg/Ca data from foraminifers retrieved from three sediment cores in the western tropical Pacific Ocean to reconstruct Holocene sea surface temperatures and salinities in the region. We find a decrease in sea surface temperatures of ~0.5 °C over the past 10,000 yr, whereas sea surface salinities decreased by ~1.5 practical salinity units. Our data imply either that the Pacific basin as a whole has become progressively less salty or that the present salinity gradient along the Equator has developed relatively recently.",
                        "author": [
                            {
                                "name": "L.D. Stott"
                            },
                            {
                                "name": "K.G. Cannariato"
                            },
                            {
                                "name": "R.C. Thunell"
                            },
                            {
                                "name": "G.H. Haug"
                            },
                            {
                                "name": "A. Koutavas"
                            },
                            {
                                "name": "S.P. Lund"
                            }
                        ],
                        "journal": "Nature",
                        "pages": "56-59",
                        "pubDataUrl": "Manually Entered",
                        "title": "Decline of surface temperature and salinity in the western tropical Pacific Ocean in the Holocene epoch.",
                        "volume": "431",
                        "identifier": []
                    }
                ],
                "studyName": "Western Tropical Pacific Holocene Sea Surface Temperature and Salinity Reconstructions"
            },
            "pretty": "{\n  \"archiveType\": \"marine sediment\",\n  \"geo\": {\n    \"geometry\": {\n      \"coordinates\": [\n        125.39,\n        -10.59,\n        -832\n      ],\n      \"type\": \"Point\"\n    },\n    \"properties\": {\n      \"siteName\": \"MD98-2170\"\n    },\n    \"type\": \"Feature\"\n  },\n  \"investigator\": [\n    {\n      \"name\": \"L.D. Stott\"\n    },\n    {\n      \"name\": \"K.G. Cannariato\"\n    },\n    {\n      \"name\": \"R.C. Thunell\"\n    },\n    {\n      \"name\": \"G.H. Haug\"\n    },\n    {\n      \"name\": \"A. Koutavas\"\n    },\n    {\n      \"name\": \"S.P. Lund\"\n    }\n  ],\n  \"description\": \"Western Tropical Pacific Holocene Sea Surface Temperature and Salinity Reconstructions. delta O18 PDB (Globigerinoides ruber); Magnesium/Calcium ratio (Globigerinoides ruber); Sea Surface Temperature (C); delta O18 SMOW (water); radiocarbon years before 1950AD\",\n  \"chronData\": [\n    {\n      \"chronMeasurementTable\": [\n        {\n          \"chronDataTableName\": \"chron1measurement1\",\n          \"filename\": \"MD98-2170.Stott.2004.chron1measurement1.csv\",\n          \"columns\": [\n            {\n              \"number\": \"1\",\n              \"variableName\": \"depth\",\n              \"variableType\": \"measured\"\n            },\n            {\n              \"number\": \"2\",\n              \"variableName\": \"labcode\",\n              \"takenAtDepth\": {\n                \"foundInTable\": \"MD98-2170.Stott.2004.chron1measurement1\",\n                \"hasColumnNumber\": \"1\",\n                \"name\": \"depth\"\n              },\n              \"variableType\": \"measured\"\n            },\n            {\n              \"number\": \"3\",\n              \"variableName\": \"mat\",\n              \"takenAtDepth\": {\n                \"foundInTable\": \"MD98-2170.Stott.2004.chron1measurement1\",\n                \"hasColumnNumber\": \"1\",\n                \"name\": \"depth\"\n              },\n              \"variableType\": \"measured\"\n            },\n            {\n              \"number\": \"4\",\n              \"units\": \"yr BP\",\n              \"measuredOn\": {\n                \"archiveName\": \"MD98-2170\",\n                \"sensingWith\": \"Globigerinoides sacculifer\"\n              },\n              \"variableName\": \"age14c\",\n              \"onProxyObservationProperty\": \"Radiocarbon\",\n              \"takenAtDepth\": {\n                \"foundInTable\": \"MD98-2170.Stott.2004.chron1measurement1\",\n                \"hasColumnNumber\": \"1\",\n                \"name\": \"depth\"\n              },\n              \"variableType\": \"measured\",\n              \"uncertainty\": 0,\n              \"hasUnits\": \"yr BP\",\n              \"uncertaintyLevel\": \"1 sigma\"\n            },\n            {\n              \"number\": \"5\",\n              \"variableName\": \"age14cuncertainty\",\n              \"takenAtDepth\": \".depth\",\n              \"variableType\": \"measured\"\n            }\n          ],\n          \"missingValue\": \"NaN\"\n        }\n      ]\n    }\n  ],\n  \"paleoData\": [\n    {\n      \"paleoMeasurementTable\": [\n        {\n          \"filename\": \"MD98-2170.Stott.2004.paleo1measurement1.csv\",\n          \"columns\": [\n            {\n              \"description\": \"depth (cm)\",\n              \"number\": \"1\",\n              \"units\": \"cm\",\n              \"variableName\": \"depth\",\n              \"variableType\": \"measured\"\n            },\n            {\n              \"description\": \"age yr BP\",\n              \"number\": \"2\",\n              \"missingValue\": \"-999\",\n              \"units\": \"yr BP\",\n              \"max\": 14575.9,\n              \"min\": 0,\n              \"variableName\": \"age\",\n              \"onInferredVariableProperty\": \"Age\",\n              \"takenAtDepth\": {\n                \"description\": \"depth (cm)\",\n                \"foundInTable\": \"MD98-2170.Stott.2004.paleo1measurement1\",\n                \"hasColumnNumber\": \"1\",\n                \"hasUnits\": \"cm\",\n                \"name\": \"depth\"\n              },\n              \"variableType\": \"inferred\"\n            },\n            {\n              \"description\": \"d18O PDB\",\n              \"number\": \"3\",\n              \"missingValue\": \"-999\",\n              \"units\": \"per mil\",\n              \"measuredOn\": {\n                \"archiveName\": \"MD98-2170\",\n                \"sensingWith\": {\n                  \"sensorGenus\": \"Globigerinoides\",\n                  \"sensorSpecies\": \"ruber\"\n                }\n              },\n              \"measurementMaterial\": \"Globigerinoides ruber\",\n              \"variableName\": \"d18o\",\n              \"onProxyObservationProperty\": \"D18O\",\n              \"measurementStandard\": \"VPDB\",\n              \"takenAtDepth\": {\n                \"description\": \"depth (cm)\",\n                \"foundInTable\": \"MD98-2170.Stott.2004.paleo1measurement1\",\n                \"hasColumnNumber\": \"1\",\n                \"hasUnits\": \"cm\",\n                \"name\": \"depth\"\n              },\n              \"variableType\": \"measured\"\n            },\n            {\n              \"description\": \"d18O SMOW\",\n              \"number\": \"4\",\n              \"missingValue\": \"-999\",\n              \"units\": \"per mil SMOW\",\n              \"measurementMaterial\": \"water\",\n              \"variableName\": \"d18ow\",\n              \"onInferredVariableProperty\": \"D18Osw\",\n              \"takenAtDepth\": {\n                \"description\": \"depth (cm)\",\n                \"foundInTable\": \"MD98-2170.Stott.2004.paleo1measurement1\",\n                \"hasColumnNumber\": \"1\",\n                \"hasUnits\": \"cm\",\n                \"name\": \"depth\"\n              },\n              \"variableType\": \"inferred\"\n            },\n            {\n              \"description\": \"Mg/Ca ratio\",\n              \"number\": \"5\",\n              \"missingValue\": \"-999\",\n              \"units\": \"mmol/mol\",\n              \"measuredOn\": {\n                \"archiveName\": \"MD98-2170\",\n                \"sensingWith\": {\n                  \"sensorGenus\": \"Globigerinoides\",\n                  \"sensorSpecies\": \"ruber\"\n                }\n              },\n              \"variableName\": \"mg\",\n              \"onProxyObservationProperty\": \"Mg/Ca\",\n              \"takenAtDepth\": {\n                \"description\": \"depth (cm)\",\n                \"foundInTable\": \"MD98-2170.Stott.2004.paleo1measurement1\",\n                \"hasColumnNumber\": \"1\",\n                \"hasUnits\": \"cm\",\n                \"name\": \"depth\"\n              },\n              \"variableType\": \"measured\"\n            },\n            {\n              \"description\": \"Mg/Ca sea surface temperature\",\n              \"number\": \"6\",\n              \"missingValue\": \"-999\",\n              \"units\": \"deg C\",\n              \"variableName\": \"sst\",\n              \"onInferredVariableProperty\": \"SST\",\n              \"takenAtDepth\": {\n                \"description\": \"depth (cm)\",\n                \"foundInTable\": \"MD98-2170.Stott.2004.paleo1measurement1\",\n                \"hasColumnNumber\": \"1\",\n                \"hasUnits\": \"cm\",\n                \"name\": \"depth\"\n              },\n              \"variableType\": \"inferred\"\n            }\n          ],\n          \"missingValue\": \"-999\",\n          \"paleoDataTableName\": \"paleo1measurement1\"\n        }\n      ]\n    }\n  ],\n  \"liPDVersion\": 1.2,\n  \"dataSetName\": \"MD98-2170.Stott.2004\",\n  \"proxy\": \"Paleoceanography\",\n  \"pub\": [\n    {\n      \"abstract\": \"In the present-day climate, surface water salinities are low in the western tropical Pacific Ocean and increase towards the eastern part of the basin. The salinity of surface waters in the tropical Pacific Ocean is thought to be controlled by a combination of atmospheric convection, precipitation, evaporation and ocean dynamics, and on interannual timescales significant variability is associated with the El Niņo/Southern Oscillation cycles. However, little is known about the variability of the coupled ocean-atmosphere system on timescales of centuries to millennia. Here we combine oxygen isotope and Mg/Ca data from foraminifers retrieved from three sediment cores in the western tropical Pacific Ocean to reconstruct Holocene sea surface temperatures and salinities in the region. We find a decrease in sea surface temperatures of ~0.5 °C over the past 10,000 yr, whereas sea surface salinities decreased by ~1.5 practical salinity units. Our data imply either that the Pacific basin as a whole has become progressively less salty or that the present salinity gradient along the Equator has developed relatively recently.\",\n      \"author\": [\n        {\n          \"name\": \"L.D. Stott\"\n        },\n        {\n          \"name\": \"K.G. Cannariato\"\n        },\n        {\n          \"name\": \"R.C. Thunell\"\n        },\n        {\n          \"name\": \"G.H. Haug\"\n        },\n        {\n          \"name\": \"A. Koutavas\"\n        },\n        {\n          \"name\": \"S.P. Lund\"\n        }\n      ],\n      \"journal\": \"Nature\",\n      \"pages\": \"56-59\",\n      \"pubDataUrl\": \"Manually Entered\",\n      \"title\": \"Decline of surface temperature and salinity in the western tropical Pacific Ocean in the Holocene epoch.\",\n      \"volume\": \"431\",\n      \"identifier\": []\n    }\n  ],\n  \"studyName\": \"Western Tropical Pacific Holocene Sea Surface Temperature and Salinity Reconstructions\"\n}"
        },
        {
            "type": "csv",
            "filenameFull": "MD98-2170.Stott.2004/data/MD98-2170.Stott.2004.paleo1measurement1.csv",
            "filenameShort": "MD98-2170.Stott.2004.paleo1measurement1.csv",
            "data": {
                "data": [
                    [
                        "5.0",
                        "0.0",
                        "-2.828",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "7.5",
                        "96.2",
                        "-2.793",
                        "0.169",
                        "5.366",
                        "29.42"
                    ],
                    [
                        "10.0",
                        "192.3",
                        "-2.785",
                        "0.154",
                        "5.315",
                        "29.31"
                    ],
                    [
                        "12.5",
                        "288.5",
                        "-2.565",
                        "0.415",
                        "5.412",
                        "29.51"
                    ],
                    [
                        "15.0",
                        "384.6",
                        "-2.925",
                        "0.005",
                        "5.296",
                        "29.27"
                    ],
                    [
                        "17.5",
                        "480.8",
                        "-2.796",
                        "0.139",
                        "5.304",
                        "29.29"
                    ],
                    [
                        "20.0",
                        "576.9",
                        "-2.931",
                        "-0.005",
                        "5.284",
                        "29.25"
                    ],
                    [
                        "22.5",
                        "673.1",
                        "-2.955",
                        "0.021",
                        "5.401",
                        "29.49"
                    ],
                    [
                        "25.0",
                        "769.2",
                        "-2.879",
                        "0.039",
                        "5.266",
                        "29.21"
                    ],
                    [
                        "30.0",
                        "961.5",
                        "-2.983",
                        "0.018",
                        "5.458",
                        "29.61"
                    ],
                    [
                        "40.0",
                        "1346.2",
                        "-2.899",
                        "0.058",
                        "5.356",
                        "29.4"
                    ],
                    [
                        "50.0",
                        "1730.8",
                        "-2.756",
                        "0.254",
                        "5.477",
                        "29.65"
                    ],
                    [
                        "65.0",
                        "2307.7",
                        "-2.918",
                        "-0.004",
                        "5.258",
                        "29.19"
                    ],
                    [
                        "80.0",
                        "2884.6",
                        "-2.799",
                        "0.177",
                        "5.402",
                        "29.49"
                    ],
                    [
                        "90.0",
                        "3269.2",
                        "-2.808",
                        "0.174",
                        "5.413",
                        "29.52"
                    ],
                    [
                        "100.0",
                        "3653.8",
                        "-2.763",
                        "0.072",
                        "5.079",
                        "28.81"
                    ],
                    [
                        "110.0",
                        "4038.5",
                        "-2.81",
                        "0.108",
                        "5.264",
                        "29.21"
                    ],
                    [
                        "120.0",
                        "4423.1",
                        "-2.936",
                        "0.061",
                        "5.448",
                        "29.59"
                    ],
                    [
                        "130.0",
                        "4807.7",
                        "-2.583",
                        "0.212",
                        "4.996",
                        "28.62"
                    ],
                    [
                        "154.0",
                        "5730.8",
                        "-2.865",
                        "0.138",
                        "5.463",
                        "29.62"
                    ],
                    [
                        "162.0",
                        "6038.5",
                        "-2.757",
                        "0.23",
                        "5.426",
                        "29.54"
                    ],
                    [
                        "168.0",
                        "6269.2",
                        "-2.911",
                        "0.122",
                        "5.534",
                        "29.76"
                    ],
                    [
                        "174.0",
                        "6500.0",
                        "-2.78",
                        "0.25",
                        "5.53",
                        "29.75"
                    ],
                    [
                        "180.0",
                        "6730.8",
                        "NaN",
                        "NaN",
                        "5.494",
                        "29.68"
                    ],
                    [
                        "183.0",
                        "6846.2",
                        "-2.877",
                        "0.122",
                        "5.456",
                        "29.6"
                    ],
                    [
                        "200.0",
                        "7203.0",
                        "-2.833",
                        "0.093",
                        "5.288",
                        "29.25"
                    ],
                    [
                        "221.0",
                        "7897.8",
                        "-2.518",
                        "0.481",
                        "5.452",
                        "29.6"
                    ],
                    [
                        "240.0",
                        "8558.3",
                        "-2.667",
                        "0.416",
                        "5.655",
                        "30.0"
                    ],
                    [
                        "258.0",
                        "9212.1",
                        "-2.642",
                        "0.374",
                        "5.493",
                        "29.68"
                    ],
                    [
                        "283.0",
                        "10165.1",
                        "-2.563",
                        "0.553",
                        "5.736",
                        "30.16"
                    ],
                    [
                        "302.0",
                        "10670.6",
                        "-2.585",
                        "0.477",
                        "5.605",
                        "29.9"
                    ],
                    [
                        "308.0",
                        "10961.6",
                        "-2.588",
                        "0.503",
                        "5.676",
                        "30.04"
                    ],
                    [
                        "321.0",
                        "11469.9",
                        "-2.368",
                        "0.598",
                        "5.376",
                        "29.44"
                    ],
                    [
                        "327.0",
                        "11728.6",
                        "-2.552",
                        "0.383",
                        "5.305",
                        "29.29"
                    ],
                    [
                        "333.0",
                        "12034.3",
                        "-2.355",
                        "0.6",
                        "5.353",
                        "29.39"
                    ],
                    [
                        "340.0",
                        "12299.5",
                        "-2.107",
                        "0.759",
                        "5.151",
                        "28.96"
                    ],
                    [
                        "346.0",
                        "12567.8",
                        "-1.901",
                        "0.909",
                        "5.027",
                        "28.69"
                    ],
                    [
                        "358.0",
                        "13159.4",
                        "-1.868",
                        "0.996",
                        "5.146",
                        "28.95"
                    ],
                    [
                        "365.0",
                        "13437.3",
                        "-1.894",
                        "0.778",
                        "4.734",
                        "28.03"
                    ],
                    [
                        "377.0",
                        "14002.0",
                        "-1.756",
                        "0.849",
                        "4.601",
                        "27.71"
                    ],
                    [
                        "383.0",
                        "14288.9",
                        "-1.527",
                        "1.072",
                        "4.587",
                        "27.68"
                    ],
                    [
                        "389.0",
                        "14578.9",
                        "-1.024",
                        "1.502",
                        "4.447",
                        "27.33"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN",
                        "NaN"
                    ],
                    [
                        ""
                    ]
                ],
                "errors": [],
                "meta": {
                    "delimiter": ",",
                    "linebreak": "\r\n",
                    "cursor": 1825
                },
                "rows": 52,
                "cols": 6,
                "delimiter": ","
            },
            "pretty": "{\n  \"data\": [\n    [\n      \"5.0\",\n      \"0.0\",\n      \"-2.828\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"7.5\",\n      \"96.2\",\n      \"-2.793\",\n      \"0.169\",\n      \"5.366\",\n      \"29.42\"\n    ],\n    [\n      \"10.0\",\n      \"192.3\",\n      \"-2.785\",\n      \"0.154\",\n      \"5.315\",\n      \"29.31\"\n    ],\n    [\n      \"12.5\",\n      \"288.5\",\n      \"-2.565\",\n      \"0.415\",\n      \"5.412\",\n      \"29.51\"\n    ],\n    [\n      \"15.0\",\n      \"384.6\",\n      \"-2.925\",\n      \"0.005\",\n      \"5.296\",\n      \"29.27\"\n    ],\n    [\n      \"17.5\",\n      \"480.8\",\n      \"-2.796\",\n      \"0.139\",\n      \"5.304\",\n      \"29.29\"\n    ],\n    [\n      \"20.0\",\n      \"576.9\",\n      \"-2.931\",\n      \"-0.005\",\n      \"5.284\",\n      \"29.25\"\n    ],\n    [\n      \"22.5\",\n      \"673.1\",\n      \"-2.955\",\n      \"0.021\",\n      \"5.401\",\n      \"29.49\"\n    ],\n    [\n      \"25.0\",\n      \"769.2\",\n      \"-2.879\",\n      \"0.039\",\n      \"5.266\",\n      \"29.21\"\n    ],\n    [\n      \"30.0\",\n      \"961.5\",\n      \"-2.983\",\n      \"0.018\",\n      \"5.458\",\n      \"29.61\"\n    ],\n    [\n      \"40.0\",\n      \"1346.2\",\n      \"-2.899\",\n      \"0.058\",\n      \"5.356\",\n      \"29.4\"\n    ],\n    [\n      \"50.0\",\n      \"1730.8\",\n      \"-2.756\",\n      \"0.254\",\n      \"5.477\",\n      \"29.65\"\n    ],\n    [\n      \"65.0\",\n      \"2307.7\",\n      \"-2.918\",\n      \"-0.004\",\n      \"5.258\",\n      \"29.19\"\n    ],\n    [\n      \"80.0\",\n      \"2884.6\",\n      \"-2.799\",\n      \"0.177\",\n      \"5.402\",\n      \"29.49\"\n    ],\n    [\n      \"90.0\",\n      \"3269.2\",\n      \"-2.808\",\n      \"0.174\",\n      \"5.413\",\n      \"29.52\"\n    ],\n    [\n      \"100.0\",\n      \"3653.8\",\n      \"-2.763\",\n      \"0.072\",\n      \"5.079\",\n      \"28.81\"\n    ],\n    [\n      \"110.0\",\n      \"4038.5\",\n      \"-2.81\",\n      \"0.108\",\n      \"5.264\",\n      \"29.21\"\n    ],\n    [\n      \"120.0\",\n      \"4423.1\",\n      \"-2.936\",\n      \"0.061\",\n      \"5.448\",\n      \"29.59\"\n    ],\n    [\n      \"130.0\",\n      \"4807.7\",\n      \"-2.583\",\n      \"0.212\",\n      \"4.996\",\n      \"28.62\"\n    ],\n    [\n      \"154.0\",\n      \"5730.8\",\n      \"-2.865\",\n      \"0.138\",\n      \"5.463\",\n      \"29.62\"\n    ],\n    [\n      \"162.0\",\n      \"6038.5\",\n      \"-2.757\",\n      \"0.23\",\n      \"5.426\",\n      \"29.54\"\n    ],\n    [\n      \"168.0\",\n      \"6269.2\",\n      \"-2.911\",\n      \"0.122\",\n      \"5.534\",\n      \"29.76\"\n    ],\n    [\n      \"174.0\",\n      \"6500.0\",\n      \"-2.78\",\n      \"0.25\",\n      \"5.53\",\n      \"29.75\"\n    ],\n    [\n      \"180.0\",\n      \"6730.8\",\n      \"NaN\",\n      \"NaN\",\n      \"5.494\",\n      \"29.68\"\n    ],\n    [\n      \"183.0\",\n      \"6846.2\",\n      \"-2.877\",\n      \"0.122\",\n      \"5.456\",\n      \"29.6\"\n    ],\n    [\n      \"200.0\",\n      \"7203.0\",\n      \"-2.833\",\n      \"0.093\",\n      \"5.288\",\n      \"29.25\"\n    ],\n    [\n      \"221.0\",\n      \"7897.8\",\n      \"-2.518\",\n      \"0.481\",\n      \"5.452\",\n      \"29.6\"\n    ],\n    [\n      \"240.0\",\n      \"8558.3\",\n      \"-2.667\",\n      \"0.416\",\n      \"5.655\",\n      \"30.0\"\n    ],\n    [\n      \"258.0\",\n      \"9212.1\",\n      \"-2.642\",\n      \"0.374\",\n      \"5.493\",\n      \"29.68\"\n    ],\n    [\n      \"283.0\",\n      \"10165.1\",\n      \"-2.563\",\n      \"0.553\",\n      \"5.736\",\n      \"30.16\"\n    ],\n    [\n      \"302.0\",\n      \"10670.6\",\n      \"-2.585\",\n      \"0.477\",\n      \"5.605\",\n      \"29.9\"\n    ],\n    [\n      \"308.0\",\n      \"10961.6\",\n      \"-2.588\",\n      \"0.503\",\n      \"5.676\",\n      \"30.04\"\n    ],\n    [\n      \"321.0\",\n      \"11469.9\",\n      \"-2.368\",\n      \"0.598\",\n      \"5.376\",\n      \"29.44\"\n    ],\n    [\n      \"327.0\",\n      \"11728.6\",\n      \"-2.552\",\n      \"0.383\",\n      \"5.305\",\n      \"29.29\"\n    ],\n    [\n      \"333.0\",\n      \"12034.3\",\n      \"-2.355\",\n      \"0.6\",\n      \"5.353\",\n      \"29.39\"\n    ],\n    [\n      \"340.0\",\n      \"12299.5\",\n      \"-2.107\",\n      \"0.759\",\n      \"5.151\",\n      \"28.96\"\n    ],\n    [\n      \"346.0\",\n      \"12567.8\",\n      \"-1.901\",\n      \"0.909\",\n      \"5.027\",\n      \"28.69\"\n    ],\n    [\n      \"358.0\",\n      \"13159.4\",\n      \"-1.868\",\n      \"0.996\",\n      \"5.146\",\n      \"28.95\"\n    ],\n    [\n      \"365.0\",\n      \"13437.3\",\n      \"-1.894\",\n      \"0.778\",\n      \"4.734\",\n      \"28.03\"\n    ],\n    [\n      \"377.0\",\n      \"14002.0\",\n      \"-1.756\",\n      \"0.849\",\n      \"4.601\",\n      \"27.71\"\n    ],\n    [\n      \"383.0\",\n      \"14288.9\",\n      \"-1.527\",\n      \"1.072\",\n      \"4.587\",\n      \"27.68\"\n    ],\n    [\n      \"389.0\",\n      \"14578.9\",\n      \"-1.024\",\n      \"1.502\",\n      \"4.447\",\n      \"27.33\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\",\n      \"NaN\"\n    ],\n    [\n      \"\"\n    ]\n  ],\n  \"errors\": [],\n  \"meta\": {\n    \"delimiter\": \",\",\n    \"linebreak\": \"\\r\\n\",\n    \"aborted\": false,\n    \"truncated\": false,\n    \"cursor\": 1825\n  },\n  \"rows\": 52,\n  \"cols\": 6,\n  \"delimiter\": \",\"\n}"
        }
    ]
]

sample_data_response = [
    {
        "dat": {
            "studyName": "Western Tropical Pacific Holocene Sea Surface Temperature and Salinity Reconstructions",
            "dataSetName": "MD98-2170.Stott.2004",
            "chronData": [],
            "paleoData": []
        },
        "feedback": {
            "missingTsidCt": 11,
            "wrnCt": 0,
            "errCt": 1,
            "tsidMsgs": [
                "Missing data: paleoData0paleoMeasurementTable0.column0.TSid",
            ],
            "posMsgs": [
                "Valid Bagit File"
            ],
            "errMsgs": [
                "Error message here"
            ],
            "wrnMsgs": []
        },
        "status": "PASS",
        "filename": ""

    },
    {
        "dat": {
            "studyName": "Western Tropical Pacific Holocene Sea Surface Temperature and Salinity Reconstructions",
            "dataSetName": "MD98-2170.Stott.2004",
            "chronData": [],
            "paleoData": []
        },
        "feedback": {
            "missingTsidCt": 11,
            "wrnCt": 0,
            "errCt": 1,
            "tsidMsgs": [
                "Missing data: paleoData0paleoMeasurementTable0.column0.TSid",
            ],
            "posMsgs": [
                "Valid Bagit File"
            ],
            "errMsgs": [
                "Error message here"
            ],
            "wrnMsgs": []
        },
        "status": "PASS",
        "filename": ""

    }

]
