package com.creditsense.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

public class FraudCheckResponse {

    @JsonProperty("is_fraudulent")
    private Boolean isFraudulent;

    @JsonProperty("fraud_probability")
    private Double fraudProbability;

    @JsonProperty("anomaly_score")
    private Double anomalyScore;

    @JsonProperty("risk_level")
    private String riskLevel;

    @JsonProperty("action")
    private String action;

    @JsonProperty("model_version")
    private String modelVersion;

    @JsonProperty("top_anomalous_features")
    private List<Map<String, Object>> topAnomalousFeatures;

    public FraudCheckResponse() {}

    public Boolean getIsFraudulent()          { return isFraudulent; }
    public Double getFraudProbability()       { return fraudProbability; }
    public Double getAnomalyScore()           { return anomalyScore; }
    public String getRiskLevel()              { return riskLevel; }
    public String getAction()                 { return action; }
    public String getModelVersion()           { return modelVersion; }
    public List<Map<String,Object>> getTopAnomalousFeatures() { return topAnomalousFeatures; }

    public void setIsFraudulent(Boolean v)    { this.isFraudulent = v; }
    public void setFraudProbability(Double v) { this.fraudProbability = v; }
    public void setAnomalyScore(Double v)     { this.anomalyScore = v; }
    public void setRiskLevel(String v)        { this.riskLevel = v; }
    public void setAction(String v)           { this.action = v; }
    public void setModelVersion(String v)     { this.modelVersion = v; }
    public void setTopAnomalousFeatures(List<Map<String,Object>> v) { this.topAnomalousFeatures = v; }
}