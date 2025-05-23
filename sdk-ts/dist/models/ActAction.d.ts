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
export declare const ActAction: {
    readonly Noop: "noop";
    readonly Retrain: "retrain";
    readonly Alert: "alert";
};
export type ActAction = typeof ActAction[keyof typeof ActAction];
export declare function instanceOfActAction(value: any): boolean;
export declare function ActActionFromJSON(json: any): ActAction;
export declare function ActActionFromJSONTyped(json: any, ignoreDiscriminator: boolean): ActAction;
export declare function ActActionToJSON(value?: ActAction | null): any;
export declare function ActActionToJSONTyped(value: any, ignoreDiscriminator: boolean): ActAction;
