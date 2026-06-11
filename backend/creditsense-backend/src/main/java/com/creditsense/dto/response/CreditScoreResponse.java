package com.creditsense.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

public class CreditScoreResponse {

    @JsonProperty("risk_score")
    private Double riskScore;

    @JsonProperty("risk_category")
    private String riskCategory;

    @JsonProperty("default_probability")
    private Double defaultProbability;

    @JsonProperty("confidence")
    private Double confidence;

    @JsonProperty("model_version")
    private String modelVersion;

    @JsonProperty("recommendation")
    private String recommendation;

    @JsonProperty("explanation")
    private List<Map<String, Object>> explanation;

    public CreditScoreResponse() {}

    public Double getRiskScore()               { return riskScore; }
    public String getRiskCategory()            { return riskCategory; }
    public Double getDefaultProbability()      { return defaultProbability; }
    public Double getConfidence()              { return confidence; }
    public String getModelVersion()            { return modelVersion; }
    public String getRecommendation()          { return recommendation; }
    public List<Map<String,Object>> getExplanation() { return explanation; }

    public void setRiskScore(Double v)         { this.riskScore = v; }
    public void setRiskCategory(String v)      { this.riskCategory = v; }
    public void setDefaultProbability(Double v){ this.defaultProbability = v; }
    public void setConfidence(Double v)        { this.confidence = v; }
    public void setModelVersion(String v)      { this.modelVersion = v; }
    public void setRecommendation(String v)    { this.recommendation = v; }
    public void setExplanation(List<Map<String,Object>> v) { this.explanation = v; }
}