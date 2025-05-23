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
export const ActAction = {
    Noop: 'noop',
    Retrain: 'retrain',
    Alert: 'alert'
} as const;
export type ActAction = typeof ActAction[keyof typeof ActAction];


export function instanceOfActAction(value: any): boolean {
    for (const key in ActAction) {
        if (Object.prototype.hasOwnProperty.call(ActAction, key)) {
            if (ActAction[key as keyof typeof ActAction] === value) {
                return true;
            }
        }
    }
    return false;
}

export function ActActionFromJSON(json: any): ActAction {
    return ActActionFromJSONTyped(json, false);
}

export function ActActionFromJSONTyped(json: any, ignoreDiscriminator: boolean): ActAction {
    return json as ActAction;
}

export function ActActionToJSON(value?: ActAction | null): any {
    return value as any;
}

export function ActActionToJSONTyped(value: any, ignoreDiscriminator: boolean): ActAction {
    return value as ActAction;
}

