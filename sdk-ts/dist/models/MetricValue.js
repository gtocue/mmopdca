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
 * @export
 */
export const MetricValueClassEnum = {
    S: 'S',
    A: 'A',
    B: 'B'
};
/**
 * Check if a given object implements the MetricValue interface.
 */
export function instanceOfMetricValue(value) {
    if (!('name' in value) || value['name'] === undefined)
        return false;
    if (!('_class' in value) || value['_class'] === undefined)
        return false;
    if (!('ts' in value) || value['ts'] === undefined)
        return false;
    if (!('value' in value) || value['value'] === undefined)
        return false;
    return true;
}
export function MetricValueFromJSON(json) {
    return MetricValueFromJSONTyped(json, false);
}
export function MetricValueFromJSONTyped(json, ignoreDiscriminator) {
    if (json == null) {
        return json;
    }
    return {
        'name': json['name'],
        'unit': json['unit'] == null ? undefined : json['unit'],
        'slo': json['slo'] == null ? undefined : json['slo'],
        '_class': json['class'],
        'ts': json['ts'],
        'value': json['value'],
    };
}
export function MetricValueToJSON(json) {
    return MetricValueToJSONTyped(json, false);
}
export function MetricValueToJSONTyped(value, ignoreDiscriminator = false) {
    if (value == null) {
        return value;
    }
    return {
        'name': value['name'],
        'unit': value['unit'],
        'slo': value['slo'],
        'class': value['_class'],
        'ts': value['ts'],
        'value': value['value'],
    };
}
