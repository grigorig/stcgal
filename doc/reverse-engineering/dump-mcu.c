/*
 * SPDX-License-Identifier: BSD-2-Clause
 * 
 * Copyright (c) 2022 Vincent DEFERT. All rights reserved.
 * 
 * Redistribution and use in source and binary forms, with or without 
 * modification, are permitted provided that the following conditions 
 * are met:
 * 
 * 1. Redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer.
 * 
 * 2. Redistributions in binary form must reproduce the above copyright 
 * notice, this list of conditions and the following disclaimer in the 
 * documentation and/or other materials provided with the distribution.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE 
 * COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
 * POSSIBILITY OF SUCH DAMAGE.
 */
/**
 * This program automates the procedure explained below and generates
 * on the standard output the content of the 'models' list of models.py.
 * 
 * It takes the name of the stc-isp executable as argument.
 */
/**
 * Manual procedure to read MCU definitions from a new STC-ISP executable
 * ========================================================================
 * 
 * We want to extract 2 tables from the executable, one with MCU names and 
 * the other with their characteristics, let's call them "Name Table" and 
 * "Info Table" respectively.
 * 
 * The Info Table appears first in the executable and contains references 
 * to the MCU name in the Name Table. Each entry in the Name Table is 16 
 * bytes long, 32 for the Info Table. New entries are prepended to the 
 * Info Table, and appended to the Name Table. Of course, both have the 
 * same number of entries.
 * 
 * This means that the Name Table is very easy to locate, as well as the 
 * end of the Info Table, but not its beginning, which must be calculated.
 * 
 * Finally, the field of an Info Table entry that references the MCU name 
 * is expressed as a memory address, not a file position, so we'll need to 
 * determine the base memory address of the name table.
 * 
 * 1. Dump the content of the executable in a text file.
 * 
 * hexdump -C stc-isp-v6.89G.exe > stc-isp-v6.89G.txt
 * 
 * 2. Locate the first entry of the Name Table.
 * 
 * Search for the following byte sequence:
 * 53 54 43 39 30 4c 45 35 31 36 41 44 00 00 00 00
 * (i.e. nul-terminated "STC90LE516AD" string).
 * 
 * Let's call this file position NTS (Name Table Start).
 * 
 * 3. Locate the end of the Name Table.
 * 
 * Search for the following byte sequence:
 * 55 4e 4b 4e 4f 57 4e 00 25 30 36 58 00 00 00 00
 * (i.e. nul-terminated "UNKNOWN" and "%06X" strings).
 * 
 * Let's call this file position NTE (Name Table End).
 * 
 * 4. Find the end of the Info Table.
 * 
 * Search for the following byte sequence (fixed last entry):
 * 05 46 01 00 xx xx xx xx 90 f1 00 00 00 f8 00 00
 * 00 00 00 00 00 00 00 00 00 00 01 00 00 00 00 00
 * 
 * Bytes marked as 'xx' must be ignored while searching
 * 
 * [Note: searching for '90 f1 00 00 00 f8 00 00' is sufficient.]
 * 
 * It should be followed by 32 zeroed bytes. Let's call the file position 
 * of the first zeroed byte ITE (Info Table End).
 * 
 * 5. Find the beginning of the Info Table.
 * 
 * The Info Table start with a block of 32 zeroed bytes except bytes
 * 4-7 which point at NTE, i.e. an info block pointing at the 'UNKNOWN' 
 * MCU name. It's the only reliable way to determine the location of
 * the Info Table.
 * 
 * Our first valid info block will thus be the offset of the Unknown
 * block + 32. Let's call this file position ITS (Info Table Start).
 * 
 * 6. Calculate the number of MCU definitions (i.e. Info Table entries).
 * 
 * NB_MCU = (ITE - ITS) / 32
 * 
 * 7. Determine the base memory address of the name table.
 * 
 * Let's suppose 'xx xx xx xx' is '9c f7 4a 00'. As it belongs to the Info 
 * Table entry describing the first item of the Name Table, we directly 
 * have what we're looking for, i.e. 0x004af79c.
 * 
 * NTBA = littleEndianOf32bitUnsignedInt('xx xx xx xx')
 * 
 * The index in the Name Table corresponding to a given Info Table item 
 * is thus:
 * 
 * NAME_IDX = (nameAddressFieldOfInfoTableItem - NTBA) / 0x10
 * 
 * NOTE: for some reason, the Info Table entries of the STC08XE-3V and 
 * STC08XE-5V each have 2 distinct mcuId, which gives 1115 Info Table 
 * entries for 1113 strings in the Name Table.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Must be updated with the "UNKNOWN" name offset before use.
static uint8_t infoTableStartSignature[] = {
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x00, 0x00, 
};

// 0x90, 0xf1 is the magic number of the STC90LE516AD
// We test only the last 24 byte of its 32-byte entry, as they are
// sufficiently discriminating and do not depend on a particular
// executable release.
static const uint8_t infoTableEndSignature[] = {
	0x90, 0xf1, 0x00, 0x00, 0x00, 0xf8, 0x00, 0x00, 
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
	0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 
};

// NUL-terminated "STC90LE516AD" followed by 3 NUL bytes
static const uint8_t nameTableStartSignature[] = {
	0x53, 0x54, 0x43, 0x39, 0x30, 0x4c, 0x45, 0x35, 
	0x31, 0x36, 0x41, 0x44, 0x00, 0x00, 0x00, 0x00, 
};

// NUL-terminated "UNKNOWN" and "%06X" followed by 3 NUL bytes
static const uint8_t nameTableEndSignature[] = {
	0x55, 0x4e, 0x4b, 0x4e, 0x4f, 0x57, 0x4e, 0x00, 
	0x25, 0x30, 0x36, 0x58, 0x00, 0x00, 0x00, 0x00, 
};

typedef struct {
	uint32_t flags;
	uint32_t nameAddr;
	uint32_t mcuId;
	uint32_t flashSize;
	uint32_t eepromSize;
	uint32_t eepromStartAddr; // STC89 & STC90 only. 0 means IAP.
	uint32_t totalSize;
	uint32_t unknown2;
} MCUInfo;

// Bit 1 is 1 for MCU which can accept 5V power supply voltage, be it
// exclusively or not, and 0 for low-voltage only MCU (around 3.3V).
#define FLAG_ACCEPT_5V_SUPPLY_VOLTAGE 0x00000002

// Bit 3 is 1 for so-called "IAP" MCU, meaning the start address of the
// flash portion used for EEPROM emulation can be configured.
#define FLAG_CONFIGURABLE_EEPROM_SIZE 0x00000008

// Bit 7 is 1 for MCU with an adjustable internal RC oscillator, i.e.
// that supports calibration. When bits 7 and 8 are both 0, the MCU has
// no IRCO at all (external crystal only).
#define FLAG_CONFIGURABLE_IRCO_FREQ 0x00000080

// Bit 8 is 1 for MCU with a fixed-frequency internal RC oscillator
// (the old IRC* models).
#define FLAG_FIXED_FREQUENCY_IRCO 0x00000100

// Bit 12 is 1 for MCS-251 MCU, i.e. with a flash size that can be
// larger than 64KB.
#define FLAG_IS_MCS251_MCU 0x00001000

#define SEARCH_BUFFER_LEN 8192
#define MCU_NAME_LEN 16

#define NO_MATCH -1
#define FOUND -2

// May help to guess the meaning of new flags as they are added.

static void toBits(uint32_t n, char *result) {
	*result = '\0';
	int pos = 0;
	
	for (uint32_t mask = 0x80000000; mask; mask >>= 1, pos++) {
		if (pos) {
			strcat(result, ",");
		}
		
		if (n & mask) {
			strcat(result, "1");
		} else {
			strcat(result, "0");
		}
	}
}

static void printCSVHeader(FILE *csvFile) {
	if (csvFile != NULL) {
		fprintf(csvFile, "name,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,flags (hex),mcuId,flashSize,eepromSize,eepromStartAddr,totalSize,unknown2\n");
	}
}

static void printCSVRow(FILE *csvFile, const MCUInfo *info, const char *name) {
	char flags[64];
	
	if (csvFile != NULL) {
		toBits(info->flags, flags);
		
		fprintf(
			csvFile, 
			"%s,%s,0x%08x,0x%04x,%u,%u,0x%08x,%u,0x%08x\n",
			name, 
			flags, 
			info->flags, 
			(uint16_t) info->mcuId, 
			info->flashSize, 
			info->eepromSize, 
			info->eepromStartAddr, 
			info->totalSize, 
			info->unknown2
		);
	}
}

static const char *toBool(uint32_t flags, uint32_t mask) {
	return (flags & mask) ? "True" : "False";
}

static void printMCUModel(const MCUInfo *info, const char *name) {
	printf(
		"    MCUModel(name='%s', magic=0x%04x, total=%u, code=%u, eeprom=%u, iap=%s, calibrate=%s, mcs251=%s),\n",
		name, 
		(uint16_t) info->mcuId, 
		info->totalSize, 
		info->flashSize, 
		info->eepromSize,
		toBool(info->flags, FLAG_CONFIGURABLE_EEPROM_SIZE),
		toBool(info->flags, FLAG_CONFIGURABLE_IRCO_FREQ),
		toBool(info->flags, FLAG_IS_MCS251_MCU)
	);
}

static void printUsage(const char *pgmName) {
	printf("Usage: %s <STC-ISP_executable> [<CSV_output_file>]\n", pgmName);
	printf("\n");
	printf("- STC-ISP_executable is the file from which MCU models must be extracted.\n");
	printf("Their list will be printed on the standard output.\n");
	printf("\n");
	printf("- The optional CSV_output_file will receive the MCU flags detail of each model\n");
	printf("to facilitate reverse engineering efforts.\n");
	printf("\n");
	printf("Example: %s stc-isp-v6.91Q.exe MCUFlags.csv > MCUModels.txt\n", pgmName);
}

int main(int argc, const char **argv) {
	int rc = 1;
	MCUInfo *infoTable = NULL;
	char *nameTable = NULL;
	int mcuCount = 0;
	uint32_t infoTableStartOffset = 0;
	uint32_t infoTableEndOffset = 0;
	uint32_t nameTableStartOffset = 0;
	uint32_t nameTableEndOffset = 0;
	uint32_t baseAddr = 0;
	int nameTableSize = 0;
	
	if (argc < 2) {
		fprintf(stderr, "ERROR: missing argument\n");
		printUsage(argv[0]);
		exit(1);
	}
	
	FILE *exeFile = fopen(argv[1], "rb");
	FILE *csvFile = NULL;
	
	if (exeFile != NULL) {
		if (argc > 2) {
			csvFile = fopen(argv[2], "wt");
		}
		
		rc = 2;
		uint8_t *buffer = (uint8_t *) malloc(SEARCH_BUFFER_LEN);
		
		if (buffer != NULL) {
			rc = 3;
			int infoTableEndMatch = NO_MATCH;
			int nameTableStartMatch = NO_MATCH;
			int nameTableEndMatch = NO_MATCH;
			uint32_t fileOffset = 0;
			int bytesRead = 0;
			
			while ((bytesRead = fread(buffer, 1, SEARCH_BUFFER_LEN, exeFile)) != 0) {
				for (int curByte = 0; curByte < SEARCH_BUFFER_LEN; curByte++) {
					int noMatch = 1;
					
					if (infoTableEndMatch > NO_MATCH) {
						if (infoTableEndSignature[infoTableEndMatch + 1] == buffer[curByte]) {
							infoTableEndMatch++;
							noMatch = 0;
							
							if (infoTableEndMatch == (sizeof(infoTableEndSignature) -1)) {
								infoTableEndMatch = FOUND;
								break;
							}
						} else {
							infoTableEndMatch = NO_MATCH;
						}
					}
					
					if (nameTableStartMatch > NO_MATCH) {
						if (nameTableStartSignature[nameTableStartMatch + 1] == buffer[curByte]) {
							nameTableStartMatch++;
							noMatch = 0;
							
							if (nameTableStartMatch == (sizeof(nameTableStartSignature) -1)) {
								nameTableStartMatch = FOUND;
								break;
							}
						} else {
							nameTableStartMatch = NO_MATCH;
						}
					}
					
					if (nameTableEndMatch > NO_MATCH) {
						if (nameTableEndSignature[nameTableEndMatch + 1] == buffer[curByte]) {
							nameTableEndMatch++;
							noMatch = 0;
							
							if (nameTableEndMatch == (sizeof(nameTableEndSignature) - 1)) {
								nameTableEndMatch = FOUND;
								break;
							}
						} else {
							nameTableEndMatch = NO_MATCH;
						}
					}
					
					if (noMatch) {
						if (infoTableEndMatch == NO_MATCH && infoTableEndSignature[0] == buffer[curByte]) {
							infoTableEndMatch = 0;
							infoTableEndOffset = fileOffset + curByte;
						} else if (nameTableStartMatch == NO_MATCH && nameTableStartSignature[0] == buffer[curByte]) {
							nameTableStartMatch = 0;
							nameTableStartOffset = fileOffset + curByte;
						} else if (nameTableEndMatch == NO_MATCH && nameTableEndSignature[0] == buffer[curByte]) {
							nameTableEndMatch = 0;
							nameTableEndOffset = fileOffset + curByte;
						}
					}
				}
				
				if (infoTableEndMatch == FOUND && nameTableStartMatch == FOUND && nameTableEndMatch == FOUND) {
					rc = 0;
					break;
				}
				
				fileOffset += SEARCH_BUFFER_LEN;
			}
			
			if (rc == 0) {
				// Point to the byte immediately following the table's last entry.
				infoTableEndOffset += sizeof(infoTableEndSignature);
				// Read last item of Info Table
				fseek(exeFile, infoTableEndOffset - sizeof(MCUInfo), SEEK_SET);
				MCUInfo lastItem;
				fread(&lastItem, sizeof(MCUInfo), 1, exeFile);
				// We need it now in order to calculate the memory address
				// corresponding to the UNKNOWN name.
				// We'll also need baseAddr later, anyway.
				baseAddr = lastItem.nameAddr;
				
				rc = 4;
				int infoTableStartMatch = NO_MATCH;
				uint32_t fileOffset = 0;
				int bytesRead = 0;
				*((uint32_t *)(infoTableStartSignature)) = (baseAddr - nameTableStartOffset) + nameTableEndOffset;
				fseek(exeFile, 0, SEEK_SET);
				
				while ((bytesRead = fread(buffer, 1, SEARCH_BUFFER_LEN, exeFile)) != 0) {
					for (int curByte = 0; curByte < SEARCH_BUFFER_LEN; curByte++) {
						if (infoTableStartMatch > NO_MATCH) {
							if (infoTableStartSignature[infoTableStartMatch + 1] == buffer[curByte]) {
								infoTableStartMatch++;
								
								if (infoTableStartMatch == (sizeof(infoTableStartSignature) - 1)) {
									infoTableStartMatch = FOUND;
									break;
								}
							} else {
								infoTableStartMatch = NO_MATCH;
							}
						}
						
						if (infoTableStartMatch == NO_MATCH && infoTableStartSignature[0] == buffer[curByte]) {
							infoTableStartMatch = 0;
							infoTableStartOffset = fileOffset + curByte;
						}
					}
					
					if (infoTableStartMatch == FOUND) {
						// Point to the first entry following the Unknown one.
						infoTableStartOffset += sizeof(MCUInfo) - 4;
						// Calculate number of entries while we're at it
						mcuCount = (infoTableEndOffset - infoTableStartOffset) / sizeof(MCUInfo);
						rc = 0;
						break;
					}
					
					fileOffset += SEARCH_BUFFER_LEN;
				}
			}
			
			free(buffer);
			
			if (rc == 0) {
				nameTableSize = nameTableEndOffset - nameTableStartOffset;
				
				nameTable = (char *) malloc(nameTableSize);
				
				if (nameTable == NULL) {
					rc = 5;
				}
			}
			
			if (rc == 0) {
				fseek(exeFile, nameTableStartOffset, SEEK_SET);
				fread(nameTable, nameTableSize, 1, exeFile);
				
				infoTable = (MCUInfo *) malloc(infoTableEndOffset - infoTableStartOffset);
				
				if (infoTable != NULL) {
					fseek(exeFile, infoTableStartOffset, SEEK_SET);
					fread(infoTable, infoTableEndOffset - infoTableStartOffset, 1, exeFile);
					
				} else {
					rc = 6;
					free(nameTable);
				}
			}
		}
		
		fclose(exeFile);
	}
	
	if (rc == 0) {
		printCSVHeader(csvFile);
		
		for (int mcu = 0; mcu < mcuCount; mcu++) {
			const char *mcuName = &nameTable[infoTable[mcu].nameAddr - baseAddr];
			
			if (strncmp(mcuName, "STC12C54", 8) == 0 || strncmp(mcuName, "STC12LE54", 9) == 0) {
				// STC12x54xx always have 12KB EEPROM
				infoTable[mcu].eepromSize = 12 * 1024;
			}
			
			printCSVRow(csvFile, &infoTable[mcu], mcuName);
			printMCUModel(&infoTable[mcu], mcuName);
		}
		
		free(infoTable);
		free(nameTable);
	}
	
	if (csvFile != NULL) {
		fclose(csvFile);
	}
	
	return rc;
}
