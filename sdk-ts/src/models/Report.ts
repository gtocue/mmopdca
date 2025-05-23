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

import { mapValues } from '../runtime';
import type { CheckReport } from './CheckReport';
import {
    CheckReportFromJSON,
    CheckReportFromJSONTyped,
    CheckReportToJSON,
    CheckReportToJSONTyped,
} from './CheckReport';
import type { ReportAnyOfValue } from './ReportAnyOfValue';
import {
    ReportAnyOfValueFromJSON,
    ReportAnyOfValueFromJSONTyped,
    ReportAnyOfValueToJSON,
    ReportAnyOfValueToJSONTyped,
} from './ReportAnyOfValue';

/**
 * メトリクス JSON (タスク完了前は None)
 * @export
 * @interface Report
 */
export interface Report {
    /**
     * 決定係数
     * @type {number}
     * @memberof Report
     */
    r2: number;
    /**
     * 合格ライン
     * @type {number}
     * @memberof Report
     */
    threshold: number;
    /**
     * 閾値をクリアしたら True
     * @type {boolean}
     * @memberof Report
     */
    passed: boolean;
}

/**
 * Check if a given object implements the Report interface.
 */
export function instanceOfReport(value: object): value is Report {
    if (!('r2' in value) || value['r2'] === undefined) return false;
    if (!('threshold' in value) || value['threshold'] === undefined) return false;
    if (!('passed' in value) || value['passed'] === undefined) return false;
    return true;
}

export function ReportFromJSON(json: any): Report {
    return ReportFromJSONTyped(json, false);
}

export function ReportFromJSONTyped(json: any, ignoreDiscriminator: boolean): Report {
    if (json == null) {
        return json;
    }
    return {
        
        'r2': json['r2'],
        'threshold': json['threshold'],
        'passed': json['passed'],
    };
}

export function ReportToJSON(json: any): Report {
    return ReportToJSONTyped(json, false);
}

export function ReportToJSONTyped(value?: Report | null, ignoreDiscriminator: boolean = false): any {
    if (value == null) {
        return value;
    }

    return {
        
        'r2': value['r2'],
        'threshold': value['threshold'],
        'passed': value['passed'],
    };
}

