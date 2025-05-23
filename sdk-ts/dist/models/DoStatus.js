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
 *
 * @export
 */
export const DoStatus = {
    Pending: 'PENDING',
    Running: 'RUNNING',
    Done: 'DONE',
    Failed: 'FAILED'
};
export function instanceOfDoStatus(value) {
    for (const key in DoStatus) {
        if (Object.prototype.hasOwnProperty.call(DoStatus, key)) {
            if (DoStatus[key] === value) {
                return true;
            }
        }
    }
    return false;
}
export function DoStatusFromJSON(json) {
    return DoStatusFromJSONTyped(json, false);
}
export function DoStatusFromJSONTyped(json, ignoreDiscriminator) {
    return json;
}
export function DoStatusToJSON(value) {
    return value;
}
export function DoStatusToJSONTyped(value, ignoreDiscriminator) {
    return value;
}
