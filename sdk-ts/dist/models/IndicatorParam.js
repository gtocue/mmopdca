/* tslint:disable */
/* eslint-disable */
/**
 * mmopdca API
 * Command-DSL-driven forecasting micro-service API only
 *
 * The version of the OpenAPI document: 0.4.0
 * Contact: gtocue510@gmail.com
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */
/**
 * Check if a given object implements the IndicatorParam interface.
 */
export function instanceOfIndicatorParam(value) {
    return true;
}
export function IndicatorParamFromJSON(json) {
    return IndicatorParamFromJSONTyped(json, false);
}
export function IndicatorParamFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
        return json;
    }
    return {
        'name': json['name'] == null ? undefined : json['name'],
        'window': json['window'] == null ? undefined : json['window'],
    };
}
export function IndicatorParamToJSON(json) {
    return IndicatorParamToJSONTyped(json, false);
}
export function IndicatorParamToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
        return value;
    }
    return {
        'name': value['name'],
        'window': value['window'],
    };
}
