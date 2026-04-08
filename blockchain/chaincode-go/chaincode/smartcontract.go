package chaincode

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

type SmartContract struct {
	contractapi.Contract
}

type SensorRecord struct {
	RecordID     string   `json:"recordID"`
	DeviceID     string   `json:"deviceID"`
	AssetType    string   `json:"assetType"`
	OrgMSP       string   `json:"orgMSP"`
	DataHash     string   `json:"dataHash"`
	IsAnomaly    bool     `json:"isAnomaly"`
	AnomalyScore float64  `json:"anomalyScore"`
	Threshold    float64  `json:"threshold"`
	FeatureKeys  []string `json:"featureKeys"`
	Timestamp    string   `json:"timestamp"`
	CommittedAt  string   `json:"committedAt"`
	RecordType   string   `json:"recordType"`
}

type MaintenanceEvent struct {
	EventID     string `json:"eventID"`
	DeviceID    string `json:"deviceID"`
	EngineerID  string `json:"engineerID"`
	OrgMSP      string `json:"orgMSP"`
	ReportHash  string `json:"reportHash"`
	EventType   string `json:"eventType"`
	Notes       string `json:"notes"`
	Timestamp   string `json:"timestamp"`
	CommittedAt string `json:"committedAt"`
	RecordType  string `json:"recordType"`
}

type FraudFlag struct {
	FlagID       string  `json:"flagID"`
	AssetID      string  `json:"assetID"`
	FraudType    string  `json:"fraudType"`
	Confidence   float64 `json:"confidence"`
	EvidenceHash string  `json:"evidenceHash"`
	FlaggedBy    string  `json:"flaggedBy"`
	Timestamp    string  `json:"timestamp"`
	RecordType   string  `json:"recordType"`
}

func (s *SmartContract) RecordSensorData(
	ctx contractapi.TransactionContextInterface,
	deviceID string, assetType string, dataHash string,
	isAnomaly bool, anomalyScore float64, threshold float64,
	featureKeysJSON string, timestamp string,
) (*SensorRecord, error) {
	raw := fmt.Sprintf("%s:%s", deviceID, timestamp)
	recordID := fmt.Sprintf("%x", sha256.Sum256([]byte(raw)))
	existing, err := ctx.GetStub().GetState(recordID)
	if err != nil {
		return nil, fmt.Errorf("ledger read failed: %w", err)
	}
	if existing != nil {
		return nil, fmt.Errorf("record %s already exists", recordID)
	}
	mspID, err := ctx.GetClientIdentity().GetMSPID()
	if err != nil {
		return nil, fmt.Errorf("failed to get MSP ID: %w", err)
	}
	var featureKeys []string
	if err := json.Unmarshal([]byte(featureKeysJSON), &featureKeys); err != nil {
		return nil, fmt.Errorf("invalid featureKeys JSON: %w", err)
	}
	record := SensorRecord{
		RecordID: recordID, DeviceID: deviceID, AssetType: assetType,
		OrgMSP: mspID, DataHash: dataHash, IsAnomaly: isAnomaly,
		AnomalyScore: anomalyScore, Threshold: threshold,
		FeatureKeys: featureKeys, Timestamp: timestamp,
		CommittedAt: time.Now().UTC().Format(time.RFC3339),
		RecordType: "SENSOR_READING",
	}
	recordJSON, err := json.Marshal(record)
	if err != nil {
		return nil, err
	}
	if err := ctx.GetStub().PutState(recordID, recordJSON); err != nil {
		return nil, fmt.Errorf("ledger write failed: %w", err)
	}
	eventPayload, _ := json.Marshal(map[string]interface{}{
		"recordID": recordID, "deviceID": deviceID, "isAnomaly": isAnomaly,
	})
	ctx.GetStub().SetEvent("SensorDataRecorded", eventPayload)
	return &record, nil
}

func (s *SmartContract) RecordFraudFlag(
	ctx contractapi.TransactionContextInterface,
	assetID string, fraudType string, confidence float64,
	evidenceHash string, timestamp string,
) (*FraudFlag, error) {
	raw := fmt.Sprintf("%s:%s:%s", assetID, fraudType, timestamp)
	flagID := fmt.Sprintf("%x", sha256.Sum256([]byte(raw)))
	flag := FraudFlag{
		FlagID: flagID, AssetID: assetID, FraudType: fraudType,
		Confidence: confidence, EvidenceHash: evidenceHash,
		FlaggedBy: "GNN_SCHEDULER", Timestamp: timestamp,
		RecordType: "FRAUD_FLAG",
	}
	flagJSON, err := json.Marshal(flag)
	if err != nil {
		return nil, err
	}
	if err := ctx.GetStub().PutState(flagID, flagJSON); err != nil {
		return nil, fmt.Errorf("ledger write failed: %w", err)
	}
	ctx.GetStub().SetEvent("FraudFlagged", flagJSON)
	return &flag, nil
}

func (s *SmartContract) GetAnomalyEvents(
	ctx contractapi.TransactionContextInterface,
) ([]SensorRecord, error) {
	queryString := `{"selector":{"recordType":"SENSOR_READING","isAnomaly":true},"sort":[{"committedAt":"desc"}],"limit":500}`
	iterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, fmt.Errorf("anomaly query failed: %w", err)
	}
	defer iterator.Close()
	var records []SensorRecord
	for iterator.HasNext() {
		result, err := iterator.Next()
		if err != nil {
			return nil, err
		}
		var record SensorRecord
		if err := json.Unmarshal(result.Value, &record); err != nil {
			return nil, err
		}
		records = append(records, record)
	}
	return records, nil
}

func (s *SmartContract) GetFraudFlags(
	ctx contractapi.TransactionContextInterface,
) ([]FraudFlag, error) {
	queryString := `{"selector":{"recordType":"FRAUD_FLAG"},"sort":[{"timestamp":"desc"}]}`
	iterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer iterator.Close()
	var flags []FraudFlag
	for iterator.HasNext() {
		result, err := iterator.Next()
		if err != nil {
			return nil, err
		}
		var flag FraudFlag
		json.Unmarshal(result.Value, &flag)
		flags = append(flags, flag)
	}
	return flags, nil
}

func (s *SmartContract) VerifyDataIntegrity(
	ctx contractapi.TransactionContextInterface,
	recordID string, rawDataJSON string,
) (bool, error) {
	recordBytes, err := ctx.GetStub().GetState(recordID)
	if err != nil || recordBytes == nil {
		return false, fmt.Errorf("record %s not found on ledger", recordID)
	}
	var record SensorRecord
	json.Unmarshal(recordBytes, &record)
	computedHash := fmt.Sprintf("%x", sha256.Sum256([]byte(rawDataJSON)))
	return computedHash == record.DataHash, nil
}
